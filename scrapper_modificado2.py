"""
Argenprop Scraper - Ventas
- URL: departamentos en venta en Capital Federal
- Parseo de precio mejorado: ARS, USD, pesos, "Consultar", precio en detalle
- Async/concurrent con aiohttp + asyncio
- Guardado incremental en TSV
"""

import asyncio
import aiohttp
import re
import os
import time
import logging
import pandas as pd
from bs4 import BeautifulSoup

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

MAX_CONCURRENT_PAGES   = 3
MAX_CONCURRENT_DETAILS = 8
SAVE_EVERY             = 50
DELAY_BETWEEN_REQUESTS = 1.0
MAX_RETRIES            = 5
TIMEOUT_SECONDS        = 20
OUTPUT_DIR             = "output"

BASE_URL   = "https://www.argenprop.com"
SEARCH_URL = f"{BASE_URL}/departamentos/venta/capital-federal"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("argenprop_ventas")

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    if not text:
        return "N/A"
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_precio(text: str) -> str:
    if not text:
        return "Consultar"
    text = text.replace("\xa0", " ").strip()
    m = re.search(r"(USD|U\$S|u\$s)\s*([0-9][0-9.,]*)", text, re.IGNORECASE)
    if m:
        return f"USD {m.group(2).replace(',', '.')}"
    m = re.search(r"(\$|ARS)\s*([0-9][0-9.,]*)", text, re.IGNORECASE)
    if m:
        return f"ARS {m.group(2).replace(',', '.')}"
    m = re.search(r"([0-9][0-9.,]{3,})", text)
    if m:
        return f"ARS {m.group(1).replace(',', '.')}"
    return "Consultar"


def parse_expensas(text: str) -> str:
    if not text:
        return "N/A"
    m = re.search(r"\+\s*(\$|ARS)?\s*([0-9][0-9.,]*)", text, re.IGNORECASE)
    if m:
        return f"ARS {m.group(2).replace(',', '.')}"
    return "N/A"


def parse_address(address_raw: str):
    calle = altura = piso = "N/A"
    try:
        piso_match = re.search(r"[Pp]iso\s*(\w+)", address_raw)
        if piso_match:
            piso = piso_match.group(1)
            address_raw = address_raw[:piso_match.start()].strip().rstrip(",").strip()
        match = re.match(r"^(.*?)\s+(\d+)\s*$", address_raw.strip())
        if match:
            calle  = match.group(1).strip()
            altura = match.group(2).strip()
        else:
            calle = address_raw.strip()
    except Exception:
        pass
    return calle, altura, piso


def extract_smart_features(row: pd.Series) -> pd.Series:
    texto = (str(row.get("Descripción", "")) + " " + str(row.get("Detalles", ""))).lower()
    return pd.Series({
        "Smart_Amenities":         1 if any(x in texto for x in ["amenities", "piscina", "pileta", "sum", "parrilla", "gym", "sauna", "laundry"]) else 0,
        "Smart_Losa_Central":      1 if any(x in texto for x in ["losa radiante", "calefacción central", "caldera central", "piso radiante"]) else 0,
        "Smart_Luminoso":          1 if any(x in texto for x in ["luminoso", "todo luz", "vista abierta", "vista panorámica", "sol"]) else 0,
        "Smart_Balcon_Aterrazado": 1 if "aterrazado" in texto or "balcón terraza" in texto else 0,
    })

# ─── FETCH CON REINTENTOS ─────────────────────────────────────────────────────

async def fetch(session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore) -> str | None:
    async with semaphore:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    url, headers=HEADERS,
                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status == 200:
                        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
                        return await resp.text()
                    if resp.status in (403, 429):
                        wait = min(2 ** attempt, 30)
                        log.warning(f"Rate limit ({resp.status}). Esperando {wait}s...")
                        await asyncio.sleep(wait)
                    elif resp.status == 404:
                        return None
                    else:
                        wait = min(2 ** attempt, 30)
                        log.warning(f"HTTP {resp.status} intento {attempt}/{MAX_RETRIES}. Esperando {wait}s...")
                        await asyncio.sleep(wait)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                wait = min(2 ** attempt, 30)
                log.warning(f"Error intento {attempt}/{MAX_RETRIES}: {e}. Reintentando en {wait}s...")
                await asyncio.sleep(wait)
        log.error(f"Falló definitivamente: {url}")
        return None

# ─── CAPTCHA ──────────────────────────────────────────────────────────────────

def is_captcha_page(html: str) -> bool:
    if not html:
        return False
    lower = html.lower()
    return any(kw in lower for kw in [
        "recaptcha", "captcha", "robot", "challenge", "blocked",
        "acceso denegado", "access denied", "g-recaptcha",
        "verifique que no es un robot",
    ]) and "listing__item" not in lower


async def wait_for_captcha_resolution(url: str, page: int):
    print("\n" + "═" * 60)
    print(f"🚨  CAPTCHA detectado en página {page}")
    print(f"")
    print(f"👉  Abrí tu browser y navegá a:")
    print(f"    {url}")
    print(f"")
    print(f"    Resolvé el captcha, esperá los resultados,")
    print(f"    y presioná ENTER acá para continuar.")
    print("═" * 60)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input, "    > ")
    print("▶️  Continuando...\n")

# ─── PARSEO DE LISTADO ────────────────────────────────────────────────────────

def parse_listing_page(html: str) -> tuple[list[dict], bool]:
    soup      = BeautifulSoup(html, "html.parser")
    items_raw = soup.find_all("div", class_="listing__item")

    if not items_raw:
        return [], False

    items = []
    for item in items_raw:
        try:
            link_tag = item.find("a", class_="card")
            if not link_tag:
                continue
            link = BASE_URL + link_tag["href"]

            price_block = item.find("p", class_="card__price")
            price_text  = clean_text(price_block.text) if price_block else ""
            precio      = parse_precio(price_text)
            expensas    = parse_expensas(price_text)

            addr_tag    = item.find("p", class_="card__address")
            raw_address = clean_text(addr_tag.text) if addr_tag else ""
            calle, altura, piso = parse_address(raw_address)

            feat_tag = item.find("ul", class_="card__main-features")
            features = clean_text(feat_tag.text) if feat_tag else "N/A"

            items.append({
                "Precio":      precio,
                "Expensas":    expensas,
                "Calle":       calle,
                "Altura":      altura,
                "Piso":        piso,
                "Detalles":    features,
                "Descripción": "",
                "Link":        link,
            })
        except Exception:
            continue

    return items, len(items_raw) > 0

# ─── PARSEO DE DETALLE ────────────────────────────────────────────────────────

KV_FIELDS = {
    "cant. ambientes":     "Ambientes",
    "cant. dormitorios":   "Dormitorios",
    "cant. baños":         "Baños",
    "cant. toilettes":     "Toilettes",
    "estado":              "Estado",
    "antiguedad":          "Antiguedad",
    "disposición":         "Disposicion",
    "orientación":         "Orientacion",
    "tipo de balcón":      "Tipo_Balcon",
    "apto profesional":    "Apto_Profesional",
    "apto crédito":        "Apto_Credito",
    "tipo de unidad":      "Tipo_Unidad",
    "tipo de operación":   "Tipo_Operacion",
    "sup. cubierta":       "Sup_Cubierta_m2",
    "sup. total":          "Sup_Total_m2",
    "sup. descubierta":    "Sup_Descubierta_m2",
    "precio":              "Precio_Ficha",
    "expensas":            "Expensas_Ficha",
    "cant. pisos":         "Cant_Pisos_Edificio",
    "deptos. por piso":    "Deptos_Por_Piso",
    "antiguedad edificio": "Antiguedad_Edificio",
    "estado edificio":     "Estado_Edificio",
}

BINARY_FEATURES = [
    "Aire acondicionado individual", "Electricidad", "Losa radiante",
    "Gas natural", "Agua corriente", "Agua caliente",
    "Balcón", "Terraza", "Jardín", "Patio", "Baulera", "Cochera",
    "Muebles de cocina", "Lavarropas", "Lavavajillas",
    "Conexión para lavarropas", "Permite Mascotas", "Apto Crédito",
    "Apto Profesional", "Ascensor", "Pileta", "Piscina", "Parrilla",
    "SUM", "Gimnasio", "Sauna", "Laundry", "Seguridad 24hs", "Vigilancia",
    "Acceso para personas con movilidad reducida", "Pavimento", "ABL",
]
BINARY_KEYS = {f.lower(): f.replace(" ", "_") for f in BINARY_FEATURES}


def parse_detail_page(html: str, url: str = "") -> dict:
    result: dict = {"Descripción": "Sin descripción"}
    for col in KV_FIELDS.values():
        result[col] = "N/A"
    for col in BINARY_KEYS.values():
        result[col] = 0

    soup = BeautifulSoup(html, "html.parser")

    # ── Descripción ───────────────────────────────────────────────────────────
    desc_sec = soup.find("section", class_="section-description")
    if desc_sec:
        content = desc_sec.find(class_="section-description--content")
        raw = content.get_text(" ") if content else desc_sec.get_text(" ")
        result["Descripción"] = clean_text(raw).replace("Leer más Leer menos", "").strip()

    # ── Precio fallback desde detalle ─────────────────────────────────────────
    for selector in ["p.price-operation", "p.card__price", "span.price", "[class*='price']"]:
        price_el = soup.select_one(selector)
        if price_el:
            precio_det = parse_precio(clean_text(price_el.get_text()))
            if precio_det != "Consultar":
                result["Precio_Ficha"] = precio_det
                break

    # ── Features / amenities ──────────────────────────────────────────────────
    for ul in soup.find_all("ul", class_="property-features"):
        for li in ul.find_all("li"):
            li_class = li.get("class", [])

            if "property-features-item" in li_class:
                amenity = clean_text(li.get_text()).lower()
                col = BINARY_KEYS.get(amenity)
                if col:
                    result[col] = 1
                continue

            p = li.find("p")
            if not p:
                continue
            strong = p.find("strong")
            if not strong:
                continue

            strong_text = clean_text(strong.get_text())
            label_text  = clean_text(
                p.get_text().replace(strong.get_text(), "")
            ).rstrip(":").strip()

            if label_text:
                key   = label_text.lower()
                value = re.sub(r"\s*m2\s*", "", strong_text).strip()
                col   = KV_FIELDS.get(key)
                if col:
                    if col == "Precio_Ficha":
                        result[col] = parse_precio(value)
                    elif col == "Expensas_Ficha":
                        result[col] = parse_expensas(value)
                    else:
                        result[col] = value
            else:
                key = strong_text.lower()
                col = KV_FIELDS.get(key)
                if col:
                    result[col] = "Sí"
                else:
                    bin_col = BINARY_KEYS.get(key)
                    if bin_col:
                        result[bin_col] = 1

    return result

# ─── MERGE ────────────────────────────────────────────────────────────────────

def merge_item(item: dict) -> dict:
    if item.get("Precio") == "Consultar":
        ficha = item.get("Precio_Ficha", "N/A")
        if ficha and ficha not in ("N/A", "Consultar"):
            item["Precio"] = ficha
    return item

# ─── GUARDADO ─────────────────────────────────────────────────────────────────

def save_incremental(data: list[dict], filepath: str):
    df = pd.DataFrame(data)
    features_df = df.apply(extract_smart_features, axis=1)
    df = pd.concat([df, features_df], axis=1)
    df.to_csv(filepath, sep="\t", index=False, encoding="utf-8-sig")
    log.info(f"💾 {len(df)} registros → {filepath}")

# ─── SCRAPER PRINCIPAL ────────────────────────────────────────────────────────

async def scrape(max_pages: int | None = None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp   = int(time.time())
    output_file = os.path.join(OUTPUT_DIR, f"argenprop_ventas_{timestamp}.tsv")

    sem_pages   = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
    sem_details = asyncio.Semaphore(MAX_CONCURRENT_DETAILS)

    all_data:   list[dict] = []
    seen_links: set[str]   = set()

    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_PAGES + MAX_CONCURRENT_DETAILS,
        ssl=False,
    )

    async with aiohttp.ClientSession(connector=connector) as session:

        page = 1
        while True:
            if max_pages and page > max_pages:
                log.info(f"Límite de páginas alcanzado ({max_pages}).")
                break

            url  = SEARCH_URL if page == 1 else f"{SEARCH_URL}?pagina-{page}"
            log.info(f"📄 Página {page} → {url}")
            html = await fetch(session, url, sem_pages)

            if html is None:
                log.info(f"Sin respuesta en página {page}. Fin.")
                break

            if is_captcha_page(html):
                await wait_for_captcha_resolution(url, page)
                html = await fetch(session, url, sem_pages)
                if html is None or is_captcha_page(html):
                    log.error("Captcha no resuelto. Guardando y saliendo.")
                    break

            items, has_more = parse_listing_page(html)

            if not items:
                log.info(f"Sin resultados en página {page}. Fin.")
                break

            new_items = [i for i in items if i["Link"] not in seen_links]
            for i in new_items:
                seen_links.add(i["Link"])

            log.info(f"   → {len(new_items)} propiedades nuevas.")

            async def enrich(item: dict) -> dict:
                html_detail = await fetch(session, item["Link"], sem_details)
                if html_detail:
                    detail = parse_detail_page(html_detail, url=item["Link"])
                    item.update(detail)
                item = merge_item(item)
                return item

            enriched = list(await asyncio.gather(*[enrich(i) for i in new_items]))
            all_data.extend(enriched)

            log.info(f"   ✅ Total: {len(all_data)} propiedades.")

            if len(all_data) % SAVE_EVERY < len(new_items):
                save_incremental(all_data, output_file)

            if not has_more:
                log.info("No hay más páginas.")
                break

            page += 1
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    if all_data:
        save_incremental(all_data, output_file)
        log.info(f"\n🎉 Listo. {len(all_data)} propiedades en: {output_file}")
    else:
        log.warning("No se obtuvieron datos.")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Argenprop Scraper - Ventas")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    asyncio.run(scrape(max_pages=args.max_pages))