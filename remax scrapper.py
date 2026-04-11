"""
REMAX Argentina - Scraper optimizado
======================================
- Async/concurrent con aiohttp + asyncio
- Reintentos automáticos con backoff exponencial
- Recorre todas las páginas del listado (page=0, page=1, ...)
- Entra a cada publicación individual para extraer todos los campos
- Extrae campos desde el HTML estático (no necesita JS/Selenium)
- Extrae campos adicionales analizando la descripción en texto libre
- Guardado incremental en remax_datos.csv (no pierde datos si se interrumpe)
- Modo append: cada ejecución AGREGA filas, nunca sobreescribe

INSTALACIÓN:
    pip install aiohttp beautifulsoup4 lxml

USO:
    python remax_scraper.py                              # todas las páginas
    python remax_scraper.py --page-start 0 --page-end 9 # páginas 0 a 9 inclusive
    python remax_scraper.py --page-start 10              # desde página 10 hasta el final
    python remax_scraper.py --max-pages 5                # solo las primeras 5 páginas
    python remax_scraper.py --delay 0.5                  # ajustar delay entre requests

NOTA: Cada ejecución agrega filas al CSV existente sin borrar lo anterior.
      Si el archivo no existe, lo crea con el encabezado.
      Si ya existe, agrega filas directamente sin repetir el encabezado.
"""

import asyncio
import aiohttp
import re
import os
import csv
import logging
import argparse
import unicodedata
from bs4 import BeautifulSoup
from yarl import URL

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

MAX_CONCURRENT_PAGES   = 4    # Páginas del listado procesadas en paralelo
MAX_CONCURRENT_DETAILS = 12   # Detalles de publicaciones en paralelo
DELAY_BETWEEN_REQUESTS = 0.5  # Segundos de pausa entre requests (por worker)
MAX_RETRIES            = 4    # Reintentos ante error/timeout
TIMEOUT_SECONDS        = 20   # Timeout por request
OUTPUT_FILE            = "remax_datos.csv"
CALLEJERO_FILE         = "callejero.csv"  # CSV con nombres oficiales de calles

BASE_URL   = "https://www.remax.com.ar"
LISTING_URL = (
    BASE_URL + "/listings/buy"
    "?page={page}"
    "&pageSize=24"
    "&sort=-createdAt"
    "&in:operationId=1"
    "&in:eStageId=0,1,2,3,4"
    "&locations=in:CF@%3Cb%3ECapital%3C%2Fb%3E%20%3Cb%3EFed%3C%2Fb%3Eeral::::::"
    "&landingPath="
    "&filterCount=0"
    "&viewMode=listViewMode"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": BASE_URL,
}

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
    """Minúsculas, sin tildes, sin puntuación extra."""
    text = text.upper().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Quitar prefijos comunes que REMAX suele omitir o agregar
    text = re.sub(r"^(AV\.|AVDA\.|AVENIDA|PJE\.|PASAJE|AUTOPISTA)\s+", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _levenshtein(a: str, b: str) -> int:
    """Distancia de edición entre dos strings."""
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
    """
    Carga el callejero y devuelve lista de (nombre_normalizado, nombre_oficial).
    Usa 'nomoficial' como nombre canónico.
    """
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


# Se carga una sola vez al iniciar el módulo
_CALLEJERO: list[tuple[str, str]] = []
# Índice invertido: primera palabra → candidatos (para acelerar búsqueda)
_CALLE_INDEX: dict[str, list[tuple[str, str]]] = {}


def load_callejero():
    global _CALLEJERO, _CALLE_INDEX
    _CALLEJERO = _load_callejero(CALLEJERO_FILE)
    for norm, oficial in _CALLEJERO:
        first_word = norm.split()[0] if norm.split() else ""
        _CALLE_INDEX.setdefault(first_word, []).append((norm, oficial))


def match_calle(raw: str) -> str:
    """
    Dado el nombre de calle extraído del título, devuelve el nombre oficial
    del callejero más cercano. Si no hay callejero cargado, devuelve raw.
    """
    if not _CALLEJERO:
        return raw

    query = _normalize(raw)
    if not query:
        return raw

    # 1) Búsqueda exacta primero (más rápida)
    for norm, oficial in _CALLEJERO:
        if norm == query:
            return oficial

    # 2) Buscar candidatos por primera palabra para reducir el espacio
    first_word = query.split()[0] if query.split() else ""
    candidates = _CALLE_INDEX.get(first_word, _CALLEJERO)

    # 3) Distancia de Levenshtein sobre los candidatos
    # Umbral: toleramos hasta 30% del largo del query o 4 caracteres
    threshold = max(4, int(len(query) * 0.30))
    best_dist = threshold + 1
    best_name = raw

    for norm, oficial in candidates:
        # Optimización: si la diferencia de largo es mayor al umbral, saltar
        if abs(len(norm) - len(query)) > threshold:
            continue
        dist = _levenshtein(query, norm)
        if dist < best_dist:
            best_dist = dist
            best_name = oficial

    return best_name


def parse_address(raw: str):
    """Separa 'Calle Altura, Piso X' en sus partes."""
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

# ─── FETCH CON REINTENTOS ─────────────────────────────────────────────────────

async def fetch(session: aiohttp.ClientSession, url: str, sem: asyncio.Semaphore) -> str | None:
    async with sem:
        # Usar yarl.URL con encoded=True para que aiohttp no re-encodee los caracteres especiales
        parsed = URL(url, encoded=True)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    parsed, headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                    allow_redirects=True,
                ) as resp:
                    if resp.status == 200:
                        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
                        return await resp.text()
                    if resp.status in (403, 429):
                        wait = 2 ** attempt
                        log.warning(f"Rate limit ({resp.status}). Esperando {wait}s...")
                        await asyncio.sleep(wait)
                    elif resp.status == 404:
                        return None
                    else:
                        await asyncio.sleep(2 ** attempt)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                wait = 2 ** attempt
                log.warning(f"Error intento {attempt}/{MAX_RETRIES} [{url}]: {e}. Reintentando en {wait}s...")
                await asyncio.sleep(wait)
        log.error(f"Falló definitivamente: {url}")
        return None

# ─── PARSEO DEL LISTADO ───────────────────────────────────────────────────────

def parse_listing_page(html: str) -> tuple[list[str], int]:
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

    page_size = 24
    ps_match = re.search(r"pageSize[=:](\d+)", html)
    if ps_match:
        page_size = int(ps_match.group(1))

    return links, page_size


def get_total_pages(html: str, page_size: int) -> int:
    import math
    soup = BeautifulSoup(html, "lxml")

    h1 = soup.find("h1")
    if h1:
        m = re.search(r"([\d.,]+)\s+propiedad", h1.get_text())
        if m:
            total = int(re.sub(r"[.,]", "", m.group(1)))
            pages = math.ceil(total / page_size)
            log.info(f"Total propiedades: {total:,} → {pages} páginas (pageSize={page_size})")
            return pages

    texts = soup.find_all(string=re.compile(r"de\s+\d+", re.I))
    for t in texts:
        m = re.search(r"de\s+([\d.]+)", t)
        if m:
            return int(m.group(1).replace(".", ""))

    return 1

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

    full_text = soup.get_text(separator="\n")
    lines     = [l.strip() for l in full_text.splitlines() if l.strip()]
    text_lower = full_text.lower()

    # ── Precio y Expensas ─────────────────────────────────────────────────────
    # Buscamos en líneas individuales para no mezclar valores entre sí.
    # Precio: línea que matchea EXACTAMENTE "número moneda" (ej: "175.000 USD")
    # Expensas: línea que contiene la palabra "Expensas"
    for line in lines:
        if row["Precio"] == "N/A":
            m = re.fullmatch(r"([\d.,]+)\s*(USD|ARS|\$)", line.strip())
            if m:
                row["Precio"] = f"{m.group(1)} {m.group(2)}"
        if row["Expensas"] == "N/A":
            m = re.search(r"[Ee]xpensas\s*[:\-]?\s*([\d.,]+)\s*(ARS|USD|\$)?", line)
            if m:
                row["Expensas"] = f"{m.group(1)} {m.group(2) or 'ARS'}"

    # ── Dirección ─────────────────────────────────────────────────────────────
    # El <title> tiene: "Casa en venta 5 ambientes en San Pedro 7100, Barrio, Ciudad"
    # Hay dos "en": el primero es "en venta", el segundo precede a la dirección.
    page_title = soup.find("title")
    if page_title:
        t = page_title.get_text()
        # Buscar el SEGUNDO "en " que precede a la dirección
        matches = list(re.finditer(r"\ben\s+", t, re.IGNORECASE))
        if len(matches) >= 2:
            addr_start = matches[-1].end()
            addr_raw   = t[addr_start:].split(",")[0].strip()
            calle, altura, piso = parse_address(addr_raw)
            row["Calle"]  = match_calle(calle) if calle != "N/A" else "N/A"
            row["Altura"] = altura
            row["Piso"]   = piso

    # ── Campos KV estrictos ───────────────────────────────────────────────────
    # REMAX muestra cada dato en su propia línea con formato exacto:
    # "superficie total: 800 m²" / "ambientes: 4" / "baños: 2" etc.
    # Usamos match desde el inicio de línea (^) para evitar capturar basura.
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

    # ── Amenities binarios ────────────────────────────────────────────────────
    # Primero buscamos coincidencia exacta de línea (más preciso)
    lines_set = {l.lower().strip() for l in lines}
    for keyword, col in BINARY_MAP.items():
        if col in row and keyword in lines_set:
            row[col] = 1

    # Luego búsqueda substring solo para keywords largos (evita falsos positivos)
    for keyword, col in BINARY_MAP.items():
        if col not in row or row[col] == 1:
            continue
        if len(keyword) > 5 and keyword in text_lower:
            row[col] = 1

    # ── Smart features ────────────────────────────────────────────────────────
    row.update(smart_features(text_lower))

    return row

# ─── CSV (modo append) ────────────────────────────────────────────────────────

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

def close_csv():
    if _csv_file:
        _csv_file.close()

# ─── SCRAPER PRINCIPAL ────────────────────────────────────────────────────────

async def scrape(page_start: int, page_end: int | None, delay: float):
    global DELAY_BETWEEN_REQUESTS
    DELAY_BETWEEN_REQUESTS = delay

    sem_pages   = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
    sem_details = asyncio.Semaphore(MAX_CONCURRENT_DETAILS)
    seen_links: set[str] = set()
    total_written = 0
    buffer: list[dict] = []

    load_callejero()

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_PAGES + MAX_CONCURRENT_DETAILS,
        ssl=False,
        ttl_dns_cache=300,
    )

    init_csv(OUTPUT_FILE)

    async with aiohttp.ClientSession(connector=connector) as session:

        # ── Cargar página de referencia para detectar el total ────────────────
        # Siempre cargamos page=0 para saber cuántas páginas hay en total,
        # pero solo procesamos el rango indicado por el usuario.
        log.info(f"Cargando página 0 para detectar total de páginas...")
        html_ref = await fetch(session, LISTING_URL.format(page=0), sem_pages)
        if not html_ref:
            log.error("No se pudo cargar la primera página. Abortando.")
            return

        _, page_size  = parse_listing_page(html_ref)
        total_pages   = get_total_pages(html_ref, page_size)

        # Determinar rango efectivo
        start = page_start
        end   = min(page_end, total_pages - 1) if page_end is not None else total_pages - 1

        if start > end:
            log.error(f"Rango inválido: page-start={start} > page-end={end} (total páginas={total_pages})")
            return

        log.info(f"Rango a procesar: páginas {start} a {end} ({end - start + 1} páginas)")

        # Si page_start == 0 reutilizamos el html ya descargado
        html0 = html_ref if start == 0 else None

        # ── Procesar una página ───────────────────────────────────────────────
        async def process_page(page: int) -> list[dict]:
            if page == 0 and html0 is not None:
                html = html0
            else:
                html = await fetch(session, LISTING_URL.format(page=page), sem_pages)
                if not html:
                    log.warning(f"Página {page}: sin respuesta.")
                    return []

            links, _ = parse_listing_page(html)
            new_links = [l for l in links if l not in seen_links]
            for l in new_links:
                seen_links.add(l)

            if not new_links:
                log.info(f"Página {page+1}: sin publicaciones nuevas.")
                return []

            log.info(f"Página {page+1}/{total_pages} → {len(new_links)} publicaciones")

            async def fetch_detail(url: str) -> dict:
                html_d = await fetch(session, url, sem_details)
                if not html_d:
                    row = empty_row()
                    row["Link"] = url
                    return row
                return parse_detail(html_d, url)

            return list(await asyncio.gather(*[fetch_detail(l) for l in new_links]))

        # ── Procesar en batches ───────────────────────────────────────────────
        pages = list(range(start, end + 1))
        for i in range(0, len(pages), MAX_CONCURRENT_PAGES):
            batch = pages[i:i + MAX_CONCURRENT_PAGES]
            results = await asyncio.gather(*[process_page(p) for p in batch])
            for rows in results:
                buffer.extend(rows)
                total_written += len(rows)
            save_rows(buffer)
            log.info(f"💾 Guardado — acumulado esta ejecución: {total_written:,} propiedades")
            buffer.clear()

    close_csv()
    log.info(f"\n✅ Listo. {total_written:,} propiedades agregadas en: {os.path.abspath(OUTPUT_FILE)}")

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="REMAX Argentina Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python remax_scraper.py                              # todas las páginas
  python remax_scraper.py --page-start 0 --page-end 9 # páginas 0 a 9
  python remax_scraper.py --page-start 100             # desde página 100 hasta el final
  python remax_scraper.py --page-start 0 --page-end 49 # primera mitad
  python remax_scraper.py --page-start 50              # segunda mitad
        """,
    )
    parser.add_argument(
        "--page-start", type=int, default=0,
        help="Página desde la cual empezar, inclusive (default: 0)",
    )
    parser.add_argument(
        "--page-end", type=int, default=None,
        help="Página hasta la cual llegar, inclusive (default: última página)",
    )
    parser.add_argument(
        "--delay", type=float, default=DELAY_BETWEEN_REQUESTS,
        help=f"Delay entre requests en segundos (default: {DELAY_BETWEEN_REQUESTS})",
    )
    args = parser.parse_args()

    asyncio.run(scrape(
        page_start=1,
        page_end=4,
        delay=args.delay,
    ))
