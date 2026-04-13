"""
REMAX Argentina - Scraper con Playwright (JS rendering)
========================================================
Usa un browser headless real para ejecutar el JavaScript de REMAX
antes de parsear el HTML, resolviendo el problema del contenido vacío.

INSTALACIÓN:
    pip install playwright beautifulsoup4 lxml
    playwright install chromium

USO:
    python remax_scraper.py
    python remax_scraper.py --page-start 0 --page-end 9
    python remax_scraper.py --page-start 10
    python remax_scraper.py --delay 2.0
"""

import asyncio
import re
import os
import csv
import logging
import argparse
import unicodedata
import math
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

MAX_CONCURRENT_DETAILS = 3
DELAY_BETWEEN_PAGES    = 2.0
DELAY_BETWEEN_DETAILS  = 1.0
PAGE_TIMEOUT           = 60_000   # ms
WAIT_FOR_SELECTOR      = 30_000   # ms — espera a que cargue el contenido JS
OUTPUT_FILE            = "remax_datos_alquileres.csv"
CALLEJERO_FILE         = "callejero.csv"

BASE_URL    = "https://www.remax.com.ar"
LISTING_URL = (
    BASE_URL + "/listings/rent"
    "?page={page}"
    "&pageSize=24"
    "&sort=-createdAt"
    "&in:operationId=2"
    "&in:eStageId=0,1,2,3,4"
    "&locations=in:CF@%3Cb%3ECapital%3C%2Fb%3E%20%3Cb%3EFed%3C%2Fb%3Eeral::::::"
    "&landingPath=&filterCount=0&viewMode=listViewMode"
)

# Selector que indica que la página de listado terminó de cargar
LISTING_READY_SELECTOR = "a[href*='/listings/']:not([href*='/listings/rent']):not([href*='/listings/buy']):not([href*='/listings/sell'])"

# ─── COLUMNAS DEL CSV ─────────────────────────────────────────────────────────

FIELDNAMES = [
    "Precio", "Expensas", "Calle", "Altura", "Piso",
    "Link", "Ambientes", "Dormitorios", "Baños", "Toilettes", "Estado",
    "Antiguedad", "Disposicion", "Orientacion", "Tipo_Balcon", "Apto_Profesional",
    "Apto_Credito", "Tipo_Unidad", "Tipo_Operacion", "Sup_Cubierta_m2",
    "Sup_Total_m2", "Sup_Descubierta_m2", "Precio_Ficha", "Expensas_Ficha",
    "Cant_Pisos_Edificio", "Deptos_Por_Piso", "Antiguedad_Edificio",
    "Estado_Edificio", "Aire_acondicionado_individual", "Electricidad",
    "Losa_radiante", "Gas_natural", "Agua_corriente", "Agua_caliente",
    "Balcón", "Terraza", "Jardín", "Patio", "Baulera", "Cochera",
    "Muebles_de_cocina", "Lavarropas", "Lavavajillas",
    "Conexión_para_lavarropas", "Permite_Mascotas", "Apto_Crédito",
    "Ascensor", "Pileta", "Piscina", "Parrilla", "SUM", "Gimnasio", "Sauna",
    "Laundry", "Seguridad_24hs", "Vigilancia",
    "Acceso_para_personas_con_movilidad_reducida", "Pavimento", "ABL",
    "Smart_Amenities", "Smart_Losa_Central", "Smart_Luminoso",
    "Smart_Balcon_Aterrazado",
]

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("remax")

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def clean(text) -> str:
    if not text:
        return "N/A"
    text = str(text).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()

# ─── CALLEJERO ────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.upper().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"^(AV\.|AVDA\.|AVENIDA|PJE\.|PASAJE|AUTOPISTA)\s+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j] + (ca != cb), prev[j + 1] + 1, curr[j] + 1))
        prev = curr
    return prev[-1]


def _load_callejero(path: str) -> list[tuple[str, str]]:
    entries = []
    if not os.path.isfile(path):
        log.warning(f"Callejero no encontrado en '{path}'. La calle no será normalizada.")
        return entries
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        seen = set()
        for row in reader:
            oficial = row.get("nomoficial", "").strip()
            if not oficial or oficial in seen:
                continue
            seen.add(oficial)
            entries.append((_normalize(oficial), oficial))
    log.info(f"Callejero cargado: {len(entries)} calles únicas.")
    return entries


_CALLEJERO: list[tuple[str, str]] = []
_CALLE_INDEX: dict[str, list[tuple[str, str]]] = {}


def load_callejero():
    global _CALLEJERO, _CALLE_INDEX
    _CALLEJERO = _load_callejero(CALLEJERO_FILE)
    for norm, oficial in _CALLEJERO:
        first_word = norm.split()[0] if norm.split() else ""
        _CALLE_INDEX.setdefault(first_word, []).append((norm, oficial))


def match_calle(raw: str) -> str:
    if not _CALLEJERO:
        return raw
    query = _normalize(raw)
    if not query:
        return raw
    for norm, oficial in _CALLEJERO:
        if norm == query:
            return oficial
    first_word = query.split()[0] if query.split() else ""
    candidates = _CALLE_INDEX.get(first_word, _CALLEJERO)
    threshold = max(4, int(len(query) * 0.30))
    best_dist = threshold + 1
    best_name = raw
    for norm, oficial in candidates:
        if abs(len(norm) - len(query)) > threshold:
            continue
        dist = _levenshtein(query, norm)
        if dist < best_dist:
            best_dist = dist
            best_name = oficial
    return best_name


def parse_address(raw: str):
    calle = altura = piso = "N/A"
    raw = raw.strip()
    piso_match = re.search(r"[Pp]iso\s*(\w+)", raw)
    if piso_match:
        piso = piso_match.group(1)
        raw = raw[:piso_match.start()].strip().rstrip(",").strip()
    match = re.match(r"^(.*?)\s+(\d+)\s*$", raw)
    if match:
        calle  = match.group(1).strip()
        altura = match.group(2).strip()
    else:
        calle = raw
    return calle, altura, piso


def smart_features(texto: str) -> dict:
    texto = texto.lower()
    return {
        "Smart_Amenities": 1 if any(x in texto for x in [
            "amenities", "piscina", "pileta", "sum", "parrilla",
            "gym", "gimnasio", "sauna", "laundry"
        ]) else 0,
        "Smart_Losa_Central": 1 if any(x in texto for x in [
            "losa radiante", "calefacción central", "caldera central", "piso radiante"
        ]) else 0,
        "Smart_Luminoso": 1 if any(x in texto for x in [
            "luminoso", "todo luz", "vista abierta", "vista panorámica", "sol"
        ]) else 0,
        "Smart_Balcon_Aterrazado": 1 if any(x in texto for x in [
            "aterrazado", "balcón terraza", "balcon terraza"
        ]) else 0,
    }

# ─── PARSEO DE LISTADO ────────────────────────────────────────────────────────

def parse_listing_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()
    for a in soup.select("a[href*='/listings/']"):
        href = a.get("href", "")
        if not href:
            continue
        if re.search(r"/listings/(buy|rent|sell)", href):
            continue
        if href in seen:
            continue
        seen.add(href)
        full = href if href.startswith("http") else BASE_URL + href
        links.append(full)
    return links


def get_total_pages(html: str, page_size: int = 24) -> int:
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.find("h1")
    if h1:
        m = re.search(r"([\d.,]+)\s+propiedad", h1.get_text())
        if m:
            total = int(re.sub(r"[.,]", "", m.group(1)))
            pages = math.ceil(total / page_size)
            log.info(f"Total propiedades: {total:,} → {pages} páginas")
            return pages
    # fallback: buscar en texto libre
    texts = soup.find_all(string=re.compile(r"de\s+\d+", re.I))
    for t in texts:
        m = re.search(r"de\s+([\d.]+)", t)
        if m:
            return int(m.group(1).replace(".", ""))
    return 999  # si no encuentra, asumir muchas páginas

# ─── PARSEO DE PUBLICACIÓN INDIVIDUAL ────────────────────────────────────────

BINARY_MAP = {
    "aire acondicionado":                          "Aire_acondicionado_individual",
    "aire acondicionado individual":               "Aire_acondicionado_individual",
    "electricidad":                                "Electricidad",
    "losa radiante":                               "Losa_radiante",
    "gas natural":                                 "Gas_natural",
    "agua corriente":                              "Agua_corriente",
    "agua":                                        "Agua_corriente",
    "agua caliente":                               "Agua_caliente",
    "balcón":                                      "Balcón",
    "balcon":                                      "Balcón",
    "terraza":                                     "Terraza",
    "jardín":                                      "Jardín",
    "jardin":                                      "Jardín",
    "patio":                                       "Patio",
    "baulera":                                     "Baulera",
    "cochera":                                     "Cochera",
    "muebles de cocina":                           "Muebles_de_cocina",
    "lavarropas":                                  "Lavarropas",
    "lavavajillas":                                "Lavavajillas",
    "conexión para lavarropas":                    "Conexión_para_lavarropas",
    "permite mascotas":                            "Permite_Mascotas",
    "apto crédito":                                "Apto_Crédito",
    "ascensor":                                    "Ascensor",
    "pileta":                                      "Pileta",
    "piscina":                                     "Piscina",
    "parrilla":                                    "Parrilla",
    "sum":                                         "SUM",
    "gimnasio":                                    "Gimnasio",
    "sauna":                                       "Sauna",
    "laundry":                                     "Laundry",
    "seguridad 24hs":                              "Seguridad_24hs",
    "seguridad 24":                                "Seguridad_24hs",
    "vigilancia":                                  "Vigilancia",
    "acceso para personas con movilidad reducida": "Acceso_para_personas_con_movilidad_reducida",
    "pavimento":                                   "Pavimento",
    "abl":                                         "ABL",
}

BINARY_COLS = {
    "Aire_acondicionado_individual", "Electricidad", "Losa_radiante",
    "Gas_natural", "Agua_corriente", "Agua_caliente", "Balcón", "Terraza",
    "Jardín", "Patio", "Baulera", "Cochera", "Muebles_de_cocina",
    "Lavarropas", "Lavavajillas", "Conexión_para_lavarropas",
    "Permite_Mascotas", "Apto_Crédito", "Ascensor", "Pileta", "Piscina",
    "Parrilla", "SUM", "Gimnasio", "Sauna", "Laundry", "Seguridad_24hs",
    "Vigilancia", "Acceso_para_personas_con_movilidad_reducida",
    "Pavimento", "ABL", "Smart_Amenities", "Smart_Losa_Central",
    "Smart_Luminoso", "Smart_Balcon_Aterrazado",
}


def empty_row() -> dict:
    row = {f: "N/A" for f in FIELDNAMES}
    for col in BINARY_COLS:
        row[col] = 0
    return row


def parse_detail(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    row  = empty_row()
    row["Link"] = url

    full_text  = soup.get_text(separator="\n")
    lines      = [l.strip() for l in full_text.splitlines() if l.strip()]
    text_lower = full_text.lower()

    for line in lines:
        if row["Precio"] == "N/A":
            m = re.fullmatch(r"([\d.,]+)\s*(USD|ARS|\$)", line.strip())
            if m:
                row["Precio"] = f"{m.group(1)} {m.group(2)}"
        if row["Expensas"] == "N/A":
            m = re.search(r"[Ee]xpensas\s*[:\-]?\s*([\d.,]+)\s*(ARS|USD|\$)?", line)
            if m:
                row["Expensas"] = f"{m.group(1)} {m.group(2) or 'ARS'}"

    page_title = soup.find("title")
    if page_title:
        t = page_title.get_text()
        matches = list(re.finditer(r"\ben\s+", t, re.IGNORECASE))
        if len(matches) >= 2:
            addr_start = matches[-1].end()
            addr_raw   = t[addr_start:].split(",")[0].strip()
            calle, altura, piso = parse_address(addr_raw)
            row["Calle"]  = match_calle(calle) if calle != "N/A" else "N/A"
            row["Altura"] = altura
            row["Piso"]   = piso

    KV_PATTERNS = [
        (re.compile(r"^superficie total[:\s]+([\d.,]+)"),           "Sup_Total_m2"),
        (re.compile(r"^superficie cubierta[:\s]+([\d.,]+)"),        "Sup_Cubierta_m2"),
        (re.compile(r"^superficie semi.?cubierta[:\s]+([\d.,]+)"),  "Sup_Descubierta_m2"),
        (re.compile(r"^superficie descubierta[:\s]+([\d.,]+)"),     "Sup_Descubierta_m2"),
        (re.compile(r"^superficie terreno[:\s]+([\d.,]+)"),         "Sup_Total_m2"),
        (re.compile(r"^ambientes[:\s]+(\d+)"),                      "Ambientes"),
        (re.compile(r"^ba[ñn]os[:\s]+(\d+)"),                      "Baños"),
        (re.compile(r"^toilets?[:\s]+(\d+)"),                       "Toilettes"),
        (re.compile(r"^dormitorios[:\s]+(\d+)"),                    "Dormitorios"),
        (re.compile(r"^antig[üu]edad[:\s]+(.+)"),                   "Antiguedad"),
        (re.compile(r"^expensas[:\s]+([\d.,]+\s*(?:ARS|USD|\$)?)"), "Expensas_Ficha"),
        (re.compile(r"^disposici[oó]n[:\s]+(\w+)"),                 "Disposicion"),
        (re.compile(r"^orientaci[oó]n[:\s]+(\w+)"),                 "Orientacion"),
        (re.compile(r"^tipo de balc[oó]n[:\s]+(.+)"),               "Tipo_Balcon"),
        (re.compile(r"^apto profesional[:\s]+(\w+)"),               "Apto_Profesional"),
        (re.compile(r"^apto cr[eé]dito[:\s]+(\w+)"),                "Apto_Credito"),
        (re.compile(r"^tipo de unidad[:\s]+(.+)"),                  "Tipo_Unidad"),
        (re.compile(r"^tipo de operaci[oó]n[:\s]+(.+)"),            "Tipo_Operacion"),
        (re.compile(r"^cant\.?\s*pisos[:\s]+(\d+)"),                "Cant_Pisos_Edificio"),
        (re.compile(r"^deptos\.?\s*por piso[:\s]+(\d+)"),           "Deptos_Por_Piso"),
        (re.compile(r"^antig[üu]edad\s+edificio[:\s]+(.+)"),        "Antiguedad_Edificio"),
        (re.compile(r"^estado\s+edificio[:\s]+(.+)"),               "Estado_Edificio"),
        (re.compile(r"^estado[:\s]+(.+)"),                          "Estado"),
        (re.compile(r"^precio[:\s]+([\d.,]+)"),                     "Precio_Ficha"),
    ]

    for line in lines:
        ll = line.lower().strip()
        for pattern, col in KV_PATTERNS:
            if row[col] != "N/A":
                continue
            m = pattern.match(ll)
            if m:
                val = clean(m.group(1))
                val = re.sub(r"\s*m[²2]\s*.*$", "", val).strip()
                if val:
                    row[col] = val
                break

    lines_set = {l.lower().strip() for l in lines}
    for keyword, col in BINARY_MAP.items():
        if col in row and keyword in lines_set:
            row[col] = 1
    for keyword, col in BINARY_MAP.items():
        if col not in row or row[col] == 1:
            continue
        if len(keyword) > 5 and keyword in text_lower:
            row[col] = 1

    row.update(smart_features(text_lower))
    return row

# ─── CSV ──────────────────────────────────────────────────────────────────────

_csv_file   = None
_csv_writer = None


def init_csv(path: str):
    global _csv_file, _csv_writer
    file_exists = os.path.isfile(path) and os.path.getsize(path) > 0
    _csv_file   = open(path, "a", newline="", encoding="utf-8-sig")
    _csv_writer = csv.DictWriter(_csv_file, fieldnames=FIELDNAMES)
    if not file_exists:
        _csv_writer.writeheader()
        log.info(f"CSV nuevo creado en: {os.path.abspath(path)}")
    else:
        log.info(f"CSV existente — se agregarán filas en: {os.path.abspath(path)}")
    _csv_file.flush()


def save_rows(rows: list[dict]):
    if not rows:
        return
    _csv_writer.writerows(rows)
    _csv_file.flush()
    log.info(f"💾 {len(rows)} filas guardadas.")


def close_csv():
    if _csv_file:
        _csv_file.close()

# ─── PLAYWRIGHT HELPERS ───────────────────────────────────────────────────────

async def get_page_html(page, url: str, wait_selector: str | None = None) -> str | None:
    """Navega a una URL y devuelve el HTML tras esperar el selector indicado."""
    try:
        await page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=WAIT_FOR_SELECTOR)
            except PWTimeout:
                log.warning(f"Selector '{wait_selector}' no apareció en {url[-70:]} — usando HTML parcial")
        # Pequeña pausa extra para dejar que cargue contenido lazy
        await asyncio.sleep(1.5)
        return await page.content()
    except PWTimeout:
        log.error(f"Timeout navegando a {url[-70:]}")
        return None
    except Exception as e:
        log.error(f"Error navegando a {url[-70:]}: {e}")
        return None

# ─── SCRAPER PRINCIPAL ────────────────────────────────────────────────────────

async def scrape(page_start: int, page_end: int | None, delay: float):
    global DELAY_BETWEEN_PAGES, DELAY_BETWEEN_DETAILS
    DELAY_BETWEEN_PAGES   = delay
    DELAY_BETWEEN_DETAILS = max(0.5, delay / 2)

    load_callejero()
    init_csv(OUTPUT_FILE)

    seen_links: set[str] = set()
    total_written = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="es-AR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        # ── Página para listados (una sola, secuencial) ───────────────────────
        listing_page = await context.new_page()

        # Calentar sesión
        log.info("Calentando sesión...")
        await listing_page.goto(BASE_URL, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        log.info("Sesión calentada.")

        # Detectar total de páginas
        log.info("Cargando página 0 para detectar total...")
        html0 = await get_page_html(listing_page, LISTING_URL.format(page=0), LISTING_READY_SELECTOR)
        if not html0:
            log.error("No se pudo cargar la página 0. Abortando.")
            await browser.close()
            return

        total_pages = get_total_pages(html0)
        start = page_start
        end   = min(page_end, total_pages - 1) if page_end is not None else total_pages - 1
        log.info(f"Rango: páginas {start} a {end} ({end - start + 1} páginas)")

        # ── Pool de páginas para detalles ─────────────────────────────────────
        detail_pages = [await context.new_page() for _ in range(MAX_CONCURRENT_DETAILS)]
        detail_sem   = asyncio.Semaphore(MAX_CONCURRENT_DETAILS)

        async def fetch_detail_pw(url: str, slot_page) -> dict:
            async with detail_sem:
                html = await get_page_html(slot_page, url)
                await asyncio.sleep(DELAY_BETWEEN_DETAILS)
                if not html:
                    row = empty_row()
                    row["Link"] = url
                    return row
                return parse_detail(html, url)

        # ── Iterar páginas del listado ────────────────────────────────────────
        for page_num in range(start, end + 1):
            if page_num == 0:
                html = html0
            else:
                log.info(f"Cargando página {page_num + 1}/{total_pages}...")
                html = await get_page_html(
                    listing_page,
                    LISTING_URL.format(page=page_num),
                    LISTING_READY_SELECTOR,
                )
                if not html:
                    log.warning(f"Página {page_num}: sin respuesta, saltando.")
                    continue
                await asyncio.sleep(DELAY_BETWEEN_PAGES)

            links = parse_listing_html(html)
            new_links = [l for l in links if l not in seen_links]
            for l in new_links:
                seen_links.add(l)

            if not new_links:
                log.info(f"Página {page_num + 1}: sin publicaciones nuevas.")
                continue

            log.info(f"Página {page_num + 1}/{total_pages} → {len(new_links)} publicaciones")

            # Procesar detalles en paralelo usando el pool de páginas
            tasks = [
                fetch_detail_pw(url, detail_pages[i % MAX_CONCURRENT_DETAILS])
                for i, url in enumerate(new_links)
            ]
            rows = list(await asyncio.gather(*tasks))
            save_rows(rows)
            total_written += len(rows)
            log.info(f"Acumulado esta ejecución: {total_written:,} propiedades")

        await browser.close()

    close_csv()
    log.info(f"\n✅ Listo. {total_written:,} propiedades en: {os.path.abspath(OUTPUT_FILE)}")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="REMAX Argentina Scraper (Playwright)")
    parser.add_argument("--page-start", type=int, default=0)
    parser.add_argument("--page-end",   type=int, default=None)
    parser.add_argument("--delay",      type=float, default=DELAY_BETWEEN_PAGES,
                        help=f"Delay entre páginas en segundos (default: {DELAY_BETWEEN_PAGES})")
    args = parser.parse_args()

    asyncio.run(scrape(
        page_start=args.page_start,
        page_end=args.page_end,
        delay=args.delay,
    ))
