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

INSTALACIÓN:
    pip install aiohttp beautifulsoup4 lxml

USO:
    python remax_scraper.py                    # todas las páginas
    python remax_scraper.py --max-pages 5      # solo 5 páginas (prueba)
    python remax_scraper.py --delay 0.5        # ajustar delay entre requests
"""

import asyncio
import aiohttp
import re
import os
import csv
import logging
import argparse
from bs4 import BeautifulSoup

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

MAX_CONCURRENT_PAGES   = 4    # Páginas del listado procesadas en paralelo
MAX_CONCURRENT_DETAILS = 12   # Detalles de publicaciones en paralelo
DELAY_BETWEEN_REQUESTS = 0.5  # Segundos de pausa entre requests (por worker)
MAX_RETRIES            = 4    # Reintentos ante error/timeout
TIMEOUT_SECONDS        = 20   # Timeout por request
SAVE_EVERY             = 50   # Guardar CSV cada N registros nuevos
OUTPUT_FILE            = "remax_datos.csv"

BASE_URL   = "https://www.remax.com.ar"
LISTING_URL = (
    BASE_URL + "/listings/buy"
    "?page={page}"
    "&pageSize=24"
    "&sort=-createdAt"
    "&in:operationId=1"
    "&in:eStageId=0,1,2,3,4"
    "&locations=in:BA@%3Cb%3EBuenos%3C%2Fb%3E%20%3Cb%3EAires%3C%2Fb%3E::::::"
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
    "Precio", "Expensas", "Calle", "Altura", "Piso", "Detalles", "Descripción",
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


def parse_address(raw: str):
    """Separa 'Calle Altura, Piso X' en sus partes."""
    calle = altura = piso = "N/A"
    raw = raw.strip()
    # Extraer piso si viene al final: "Calle 123, Piso 4"
    piso_match = re.search(r"[Pp]iso\s*(\w+)", raw)
    if piso_match:
        piso = piso_match.group(1)
        raw = raw[:piso_match.start()].strip().rstrip(",").strip()
    # Separar calle y altura: "Las Focas 600"
    match = re.match(r"^(.*?)\s+(\d+)\s*$", raw)
    if match:
        calle  = match.group(1).strip()
        altura = match.group(2).strip()
    else:
        calle = raw
    return calle, altura, piso


def smart_features(descripcion: str, detalles: str) -> dict:
    """Genera columnas Smart_* analizando el texto libre."""
    texto = (descripcion + " " + detalles).lower()
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
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    url, headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
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
    """
    Extrae los links de publicaciones individuales y el pageSize real.
    Retorna (links, page_size).
    """
    soup = BeautifulSoup(html, "lxml")
    links = []
    seen = set()

    for a in soup.select("a[href*='/listings/']"):
        href = a.get("href", "")
        # Solo links de publicaciones individuales (no de búsqueda ni navegación)
        if not href:
            continue
        if re.search(r"/listings/(buy|rent|sell)", href):
            continue
        if href in seen:
            continue
        seen.add(href)
        full = href if href.startswith("http") else BASE_URL + href
        links.append(full)

    # Intentar leer pageSize real desde el HTML o asumir 24
    page_size = 24
    ps_match = re.search(r"pageSize[=:](\d+)", html)
    if ps_match:
        page_size = int(ps_match.group(1))

    return links, page_size


def get_total_pages(html: str, page_size: int) -> int:
    """Calcula el total de páginas desde el total de propiedades."""
    import math
    soup = BeautifulSoup(html, "lxml")

    # Buscar "28.962 propiedades" en el h1
    h1 = soup.find("h1")
    if h1:
        m = re.search(r"([\d.,]+)\s+propiedad", h1.get_text())
        if m:
            total = int(re.sub(r"[.,]", "", m.group(1)))
            pages = math.ceil(total / page_size)
            log.info(f"Total propiedades: {total:,} → {pages} páginas (pageSize={page_size})")
            return pages

    # Fallback: leer el paginador
    texts = soup.find_all(string=re.compile(r"de\s+\d+", re.I))
    for t in texts:
        m = re.search(r"de\s+([\d.]+)", t)
        if m:
            return int(m.group(1).replace(".", ""))

    return 1

# ─── PARSEO DE PUBLICACIÓN INDIVIDUAL ────────────────────────────────────────

# Mapeo texto del HTML → columna CSV
KV_MAP = {
    "superficie total":         "Sup_Total_m2",
    "superficie cubierta":      "Sup_Cubierta_m2",
    "superficie semicubierta":  "Sup_Descubierta_m2",
    "superficie descubierta":   "Sup_Descubierta_m2",
    "superficie terreno":       "Sup_Total_m2",   # fallback si no hay sup total
    "ambientes":                "Ambientes",
    "baños":                    "Baños",
    "toilets":                  "Toilettes",
    "dormitorios":              "Dormitorios",
    "antigüedad":               "Antiguedad",
    "expensas":                 "Expensas_Ficha",
    "disposición":              "Disposicion",
    "orientación":              "Orientacion",
    "tipo de balcón":           "Tipo_Balcon",
    "apto profesional":         "Apto_Profesional",
    "apto crédito":             "Apto_Credito",
    "tipo de unidad":           "Tipo_Unidad",
    "tipo de operación":        "Tipo_Operacion",
    "cant. pisos":              "Cant_Pisos_Edificio",
    "deptos. por piso":         "Deptos_Por_Piso",
    "antigüedad edificio":      "Antiguedad_Edificio",
    "estado edificio":          "Estado_Edificio",
    "estado":                   "Estado",
    "precio":                   "Precio_Ficha",
}

# Amenities binarios: texto que aparece en la página → columna CSV
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
    "chimenea":                                    "Balcón",   # no hay columna propia, ignorar
    "internet":                                    "N/A",
    "televisión por cable":                        "N/A",
}


def empty_row() -> dict:
    """Fila vacía con todas las columnas en N/A o 0."""
    row = {f: "N/A" for f in FIELDNAMES}
    # Binarios en 0
    binary_cols = {
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
    for col in binary_cols:
        row[col] = 0
    return row


def parse_detail(html: str, url: str) -> dict:
    """Parsea una publicación individual y devuelve una fila del CSV."""
    soup = BeautifulSoup(html, "lxml")
    row  = empty_row()
    row["Link"] = url

    # ── Precio y expensas ─────────────────────────────────────────────────────
    # Buscar texto como "175.000 USD" y "Expensas : 620.000 ARS"
    full_text = soup.get_text(separator="\n")
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]

    precio_match = re.search(r"([\d.,]+)\s*(USD|ARS|\$)", full_text)
    if precio_match:
        row["Precio"] = f"{precio_match.group(1)} {precio_match.group(2)}"

    exp_match = re.search(r"[Ee]xpensas\s*[:\-]?\s*([\d.,]+)\s*(ARS|USD|\$)?", full_text)
    if exp_match:
        moneda = exp_match.group(2) or "ARS"
        row["Expensas"] = f"{exp_match.group(1)} {moneda}"

    # ── Dirección ─────────────────────────────────────────────────────────────
    # Título del <h1> o breadcrumb contiene la dirección
    h1 = soup.find("h1")
    title_text = clean(h1.get_text()) if h1 else ""

    # Buscar en el título del documento
    page_title = soup.find("title")
    if page_title:
        title_str = page_title.get_text()
        # "Casa en venta 4 ambientes en Las Focas 600, Barrancas..."
        addr_m = re.search(r"\ben\s+(.+?),", title_str)
        if addr_m:
            calle, altura, piso = parse_address(addr_m.group(1))
            row["Calle"]  = calle
            row["Altura"] = altura
            row["Piso"]   = piso

    # ── Campos KV (superficie, ambientes, etc.) ───────────────────────────────
    # El HTML tiene pares "clave: valor" o "clave\nvalor" en distintos elementos
    # Recorremos todos los textos buscando patrones conocidos
    text_lower = full_text.lower()

    for kw, col in KV_MAP.items():
        # Buscar "clave: valor" o "clave\nvalor"
        pattern = re.escape(kw) + r"[:\s]+([^\n\r,]+)"
        m = re.search(pattern, text_lower)
        if m:
            val = clean(m.group(1))
            # Limpiar unidades comunes
            val = re.sub(r"\s*m[²2]\s*", "", val).strip()
            val = re.sub(r"\s*(años?|año)\s*$", " años", val).strip()
            if val and val != "N/A":
                row[col] = val

    # ── Detalles resumidos (texto del bloque de características) ──────────────
    detalles_parts = []
    for kw in ["superficie", "ambientes", "baños", "dormitorios", "antigüedad"]:
        m = re.search(rf"({re.escape(kw)}[^\n]{{0,40}})", text_lower)
        if m:
            detalles_parts.append(clean(m.group(1)))
    row["Detalles"] = " | ".join(detalles_parts) if detalles_parts else "N/A"

    # ── Descripción larga ─────────────────────────────────────────────────────
    # Buscar el bloque de descripción (el texto más largo de la página)
    desc = "N/A"
    # Intentar con sección de descripción
    for selector in ["section.description", "div.description", "[class*='description']"]:
        tag = soup.select_one(selector)
        if tag:
            desc = clean(tag.get_text(separator=" "))
            break
    # Fallback: párrafo más largo
    if desc == "N/A":
        paragraphs = [clean(p.get_text()) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 80]
        if paragraphs:
            desc = max(paragraphs, key=len)
    row["Descripción"] = desc

    # ── Amenities / binarios ──────────────────────────────────────────────────
    # Secciones "Servicios", "Amenities", "Ambientes", "Características"
    for section_title in ["Servicios", "Amenities", "Ambientes", "Características", "Características"]:
        # Buscar el h3/h4 con ese texto y luego leer los items que siguen
        header = soup.find(lambda tag: tag.name in ["h2","h3","h4","h5","strong","b","p"]
                           and section_title.lower() in tag.get_text().lower())
        if not header:
            continue
        # Leer los elementos siguientes hasta el próximo header
        sibling = header.find_next_sibling()
        while sibling:
            item_text = clean(sibling.get_text(separator=" ")).lower()
            # Puede ser una lista o texto directo
            for li in sibling.find_all(["li", "span", "p"]) or [sibling]:
                t = clean(li.get_text()).lower()
                col = BINARY_MAP.get(t)
                if col and col != "N/A" and col in row:
                    row[col] = 1
            # También buscar en el texto completo del sibling
            col = BINARY_MAP.get(item_text)
            if col and col != "N/A" and col in row:
                row[col] = 1
            # Parar si llegamos al próximo bloque
            if sibling.name in ["h2","h3","h4","h5"] or sibling == header:
                break
            sibling = sibling.find_next_sibling()

    # Búsqueda directa de amenities en el texto completo (más robusto)
    for keyword, col in BINARY_MAP.items():
        if col == "N/A" or col not in row:
            continue
        if keyword in text_lower:
            row[col] = 1

    # ── Smart features (desde descripción + detalles) ─────────────────────────
    smart = smart_features(row["Descripción"], row["Detalles"])
    row.update(smart)

    return row

# ─── GUARDADO INCREMENTAL ────────────────────────────────────────────────────

_csv_file   = None
_csv_writer = None

def init_csv(path: str):
    global _csv_file, _csv_writer
    file_exists = os.path.isfile(path)
    _csv_file   = open(path, "a", newline="", encoding="utf-8-sig")
    _csv_writer = csv.DictWriter(_csv_file, fieldnames=FIELDNAMES)
    if not file_exists:
        _csv_writer.writeheader()
    _csv_file.flush()
    log.info(f"CSV listo en: {os.path.abspath(path)}")


def save_rows(rows: list[dict]):
    global _csv_writer, _csv_file
    if not rows:
        return
    _csv_writer.writerows(rows)
    _csv_file.flush()


def close_csv():
    global _csv_file
    if _csv_file:
        _csv_file.close()

# ─── SCRAPER PRINCIPAL ────────────────────────────────────────────────────────

async def scrape(max_pages: int | None = None, delay: float = DELAY_BETWEEN_REQUESTS):
    global DELAY_BETWEEN_REQUESTS
    DELAY_BETWEEN_REQUESTS = delay

    sem_pages   = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
    sem_details = asyncio.Semaphore(MAX_CONCURRENT_DETAILS)

    seen_links: set[str] = set()
    total_written = 0
    buffer: list[dict] = []

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_PAGES + MAX_CONCURRENT_DETAILS,
        ssl=False,
        ttl_dns_cache=300,
    )

    init_csv(OUTPUT_FILE)

    async with aiohttp.ClientSession(connector=connector) as session:

        # ── Página 0: detectar total de páginas ───────────────────────────────
        log.info("Cargando página 0 para detectar totales...")
        html0 = await fetch(session, LISTING_URL.format(page=0), sem_pages)
        if not html0:
            log.error("No se pudo cargar la primera página. Abortando.")
            return

        links0, page_size = parse_listing_page(html0)
        total_pages = get_total_pages(html0, page_size)

        if max_pages:
            total_pages = min(total_pages, max_pages)
            log.info(f"Limitado a {total_pages} páginas por --max-pages")

        log.info(f"Procesando {total_pages} páginas (pageSize={page_size})")

        # ── Función para procesar una página completa ─────────────────────────
        async def process_page(page: int) -> list[dict]:
            if page == 0:
                html = html0
                links = links0
            else:
                html = await fetch(session, LISTING_URL.format(page=page), sem_pages)
                if not html:
                    log.warning(f"Página {page}: sin respuesta.")
                    return []
                links, _ = parse_listing_page(html)

            # Filtrar duplicados
            new_links = [l for l in links if l not in seen_links]
            for l in new_links:
                seen_links.add(l)

            if not new_links:
                return []

            log.info(f"Página {page+1}/{total_pages} → {len(new_links)} publicaciones nuevas")

            # Fetch paralelo de detalles
            async def fetch_detail(url: str) -> dict:
                html_d = await fetch(session, url, sem_details)
                if not html_d:
                    row = empty_row()
                    row["Link"] = url
                    return row
                return parse_detail(html_d, url)

            rows = await asyncio.gather(*[fetch_detail(l) for l in new_links])
            return list(rows)

        # ── Procesar páginas en batches para controlar memoria ─────────────────
        BATCH = MAX_CONCURRENT_PAGES  # páginas simultáneas

        for batch_start in range(0, total_pages, BATCH):
            batch_pages = list(range(batch_start, min(batch_start + BATCH, total_pages)))
            results = await asyncio.gather(*[process_page(p) for p in batch_pages])

            for rows in results:
                buffer.extend(rows)
                total_written += len(rows)

            # Guardar buffer al CSV
            save_rows(buffer)
            log.info(f"💾 Guardado — total acumulado: {total_written:,} propiedades")
            buffer.clear()

    close_csv()
    log.info(f"\n✅ Scraping completo. {total_written:,} propiedades en: {os.path.abspath(OUTPUT_FILE)}")

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="REMAX Argentina Scraper")
    parser.add_argument(
        "--max-pages", type=int, default=None,
        help="Límite de páginas (omitir para scrapear todo)",
    )
    parser.add_argument(
        "--delay", type=float, default=DELAY_BETWEEN_REQUESTS,
        help=f"Delay entre requests en segundos (default: {DELAY_BETWEEN_REQUESTS})",
    )
    args = parser.parse_args()

    asyncio.run(scrape(max_pages=args.max_pages, delay=args.delay))
