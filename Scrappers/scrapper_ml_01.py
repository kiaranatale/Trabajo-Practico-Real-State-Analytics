import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import glob
import os
import re

# =============================================================
# CONFIGURACIÓN DE RUTAS AUTOMÁTICA
# =============================================================
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
CARPETA_ENTRADA = os.path.join(BASE_DIR, "data_raw")
ARCHIVO_FINAL   = os.path.join(BASE_DIR, "base_flipper_detallada_ml.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# =============================================================
# PARSER DEL CUADRO DE CARACTERÍSTICAS
# Maneja los DOS formatos que usa ML en sus páginas:
#
#  FORMATO A — label y value en celdas separadas:
#    <tr>
#      <th class="...label...">Superficie total</th>
#      <td class="...value...">47,05 m²</td>
#    </tr>
#
#  FORMATO B — todo en un solo elemento "Clave: Valor":
#    <li class="...row...">Orientación: Norte</li>
#    <li class="...row...">Ascensor: Sí</li>
# =============================================================

def extraer_cuadro_caracteristicas(soup):
    """
    Extrae TODOS los campos del cuadro de características de una página de ML.
    Devuelve un dict con los nombres exactos de ML como claves.
    Ejemplo: {"Superficie total": "47,05 m²", "Ascensor": "Sí", "Expensas": "140.000 ARS", ...}
    """
    datos = {}

    # ── FORMATO A: filas con th/td o divs label/value separados ──────────────
    # Busca cualquier contenedor que suene a specs/tabla de atributos
    contenedores = soup.find_all(class_=re.compile(
        r"ui-pdp-specs|ui-vip-specs|pdp-specs|andes-table|specs__table|specs-item"
    ))
    for contenedor in contenedores:
        filas = contenedor.find_all(["tr", "li", "div"],
                                    class_=re.compile(r"row|item|specs__item"))
        for fila in filas:
            # Busca label y value en subelementos
            label = fila.find(["th", "dt", "span", "div"],
                               class_=re.compile(r"label|title|key|name|term"))
            value = fila.find(["td", "dd", "span", "div"],
                               class_=re.compile(r"value|description|data|definition"))
            if label and value:
                k = label.get_text(strip=True)
                v = value.get_text(strip=True)
                if k and v:
                    datos[k] = v

    # ── FORMATO B: elemento único "Clave: Valor" ─────────────────────────────
    # Cubre el caso donde ML renderiza "Orientación: Norte" en un solo nodo
    candidatos = soup.find_all(
        class_=re.compile(r"ui-pdp-specs|specs__item|pdp-highlighted-specs|vip-specs")
    )
    for el in candidatos:
        texto = el.get_text(separator="\n", strip=True)
        for linea in texto.splitlines():
            linea = linea.strip()
            if ":" in linea:
                partes = linea.split(":", 1)
                k = partes[0].strip()
                v = partes[1].strip()
                # Solo si la clave parece un campo real (no una URL ni texto largo)
                if k and v and len(k) < 60 and len(v) < 80:
                    if k not in datos:  # Formato A tiene prioridad
                        datos[k] = v

    # ── FALLBACK AGRESIVO: busca CUALQUIER par th/td o dt/dd en la página ────
    # Por si ML cambia sus clases, capturamos cualquier tabla estructurada
    if len(datos) < 5:
        for fila in soup.find_all("tr"):
            celdas = fila.find_all(["th", "td"])
            if len(celdas) == 2:
                k = celdas[0].get_text(strip=True)
                v = celdas[1].get_text(strip=True)
                if k and v and len(k) < 60 and len(v) < 80:
                    if k not in datos:
                        datos[k] = v
        for par in soup.find_all("dt"):
            dd = par.find_next_sibling("dd")
            if dd:
                k = par.get_text(strip=True)
                v = dd.get_text(strip=True)
                if k and v and len(k) < 60:
                    if k not in datos:
                        datos[k] = v

    return datos


def extraer_precio_expensas(soup):
    """
    Extrae precio de venta y expensas desde los elementos de precio de ML,
    que están FUERA del cuadro de características (subtítulo bajo el precio).
    """
    resultado = {}

    # Precio principal (USD)
    precio_tag = soup.find(class_=re.compile(r"andes-money-amount__fraction"))
    if precio_tag:
        resultado["_precio_pagina"] = precio_tag.get_text(strip=True)

    # Expensas: aparecen como subtítulo debajo del precio
    # ML las muestra en varios contenedores posibles
    for patron in [
        r"ui-pdp-price__subtitles",
        r"ui-pdp-price__second-line",
        r"price-tag-symbol",
        r"expenses",
        r"expensas",
    ]:
        el = soup.find(class_=re.compile(patron, re.IGNORECASE))
        if el:
            texto = el.get_text(separator=" ", strip=True)
            # Busca patrón "$ XXX.XXX" o "ARS XXX" o "Expensas: $XXX"
            m = re.search(r'(?:expensas?|expenses?)[\s:$]*([0-9][0-9.,]+)', texto, re.IGNORECASE)
            if m:
                resultado["_expensas_subtitulo"] = m.group(1).strip()
                break
            # También captura el texto completo por si contiene expensas
            if re.search(r'expensas?', texto, re.IGNORECASE):
                resultado["_expensas_subtitulo_raw"] = texto[:100]
                break

    return resultado


def extraer_detalles_propiedad(url):
    """
    Scrapea una publicación de MercadoLibre y devuelve un dict con:
    - Todos los campos del cuadro de características (nombres exactos de ML)
    - Descripción larga
    - Título
    - Ubicación
    - Precio y expensas desde la zona de precios
    """
    try:
        # Los links de click1 son redirects publicitarios, no páginas de propiedades
        if "click1." in url:
            return None

        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"    ⚠️ HTTP {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        datos = {}

        # 1. Cuadro de características completo
        cuadro = extraer_cuadro_caracteristicas(soup)
        datos.update(cuadro)

        # 2. Precio y expensas desde zona de precios (fuera del cuadro)
        precios = extraer_precio_expensas(soup)
        datos.update(precios)

        # 3. Título
        titulo_tag = soup.find(class_=re.compile(r"ui-pdp-title"))
        datos['Titulo'] = titulo_tag.get_text(strip=True) if titulo_tag else "N/A"

        # 4. Ubicación
        for patron_ubi in [r"ui-pdp-media__title", r"ui-pdp-location", r"location"]:
            ubi_tag = soup.find(class_=re.compile(patron_ubi))
            if ubi_tag:
                datos['Ubicacion'] = ubi_tag.get_text(strip=True)
                break

        # 5. Descripción larga
        desc_div = soup.find(class_=re.compile(r"ui-pdp-description__content"))
        datos['Descripcion_Larga'] = desc_div.get_text(separator=" ", strip=True) if desc_div else "N/A"

        return datos

    except Exception as e:
        print(f"    ❌ Excepción: {e}")
        return None


def detectar_separador(ruta):
    """Detecta automáticamente si el CSV usa ',' o ';' como separador."""
    with open(ruta, 'r', encoding='utf-8-sig', errors='replace') as f:
        primera_linea = f.readline()
    return ';' if primera_linea.count(';') > primera_linea.count(',') else ','


# =============================================================
# PASO 1: LEER TODOS LOS CSV DE data_raw
# =============================================================
print(f"📂 Buscando archivos CSV en: {CARPETA_ENTRADA}")

if not os.path.exists(CARPETA_ENTRADA):
    os.makedirs(CARPETA_ENTRADA)
    print(f"✅ Carpeta creada. Colocá los archivos ml_crudo_p*.csv ahí y volvé a ejecutar.")
    exit()

archivos_crudos = glob.glob(os.path.join(CARPETA_ENTRADA, "*.csv"))

if not archivos_crudos:
    print(f"⚠️  No se encontraron archivos .csv en {CARPETA_ENTRADA}")
    print(f"   Contenido actual: {os.listdir(CARPETA_ENTRADA)}")
    exit()

print(f"✅ {len(archivos_crudos)} archivo(s) encontrado(s):")
lista_dfs = []
for f in archivos_crudos:
    try:
        sep = detectar_separador(f)
        df_temp = pd.read_csv(f, sep=sep, encoding='utf-8-sig')
        lista_dfs.append(df_temp)
        print(f"   📄 {os.path.basename(f)}: {len(df_temp)} filas (sep='{sep}')")
    except Exception as e:
        print(f"   ❌ Error leyendo {os.path.basename(f)}: {e}")

if not lista_dfs:
    print("❌ No se pudo leer ningún archivo. Abortando.")
    exit()


# =============================================================
# PASO 2: UNIFICAR Y DEDUPLICAR POR 'Link'
# =============================================================
df_nuevo = pd.concat(lista_dfs, ignore_index=True)

if 'Link' not in df_nuevo.columns:
    print(f"❌ Columna 'Link' no encontrada. Columnas: {list(df_nuevo.columns)}")
    exit()

antes = len(df_nuevo)
df_nuevo = df_nuevo.drop_duplicates(subset=['Link'])
print(f"\n🔗 Total filas: {antes} → tras deduplicar por Link: {len(df_nuevo)}")


# =============================================================
# PASO 3: CARGA INCREMENTAL (solo links nuevos)
# =============================================================
if os.path.exists(ARCHIVO_FINAL):
    df_existente = pd.read_csv(ARCHIVO_FINAL, encoding='utf-8-sig')
    links_procesados = set(df_existente['Link'].dropna().tolist())
    df_a_procesar = df_nuevo[~df_nuevo['Link'].isin(links_procesados)].copy()
    print(f"📋 Ya procesados: {len(links_procesados)} | Nuevos: {len(df_a_procesar)}")
else:
    df_existente = pd.DataFrame()
    df_a_procesar = df_nuevo.copy()
    print(f"🆕 Primera ejecución: {len(df_a_procesar)} propiedades a procesar")


# =============================================================
# PASO 4: SCRAPING PROFUNDO
# =============================================================
if df_a_procesar.empty:
    print("☕ Todo está al día. No hay nuevas propiedades para procesar.")
else:
    lista_detalles = []
    total = len(df_a_procesar)

    for i, url in enumerate(df_a_procesar['Link']):
        print(f"🏠 [{i+1}/{total}] {str(url)[:70]}...")
        detalles = extraer_detalles_propiedad(url)
        if detalles:
            print(f"    ✅ {len(detalles)} campos extraídos | "
                  f"Expensas: {detalles.get('Expensas','—')} | "
                  f"Baños: {detalles.get('Baños','—')} | "
                  f"Sup: {detalles.get('Superficie cubierta','—')}")
        lista_detalles.append(detalles if detalles else {})
        time.sleep(random.uniform(3, 5))

    df_detalles = pd.DataFrame(lista_detalles)

    # Une los datos crudos (Precio, Link, etc.) con los detalles scrapeados
    df_nuevos_completos = pd.concat(
        [df_a_procesar.reset_index(drop=True), df_detalles.reset_index(drop=True)],
        axis=1
    )

    df_final_consolidado = pd.concat([df_existente, df_nuevos_completos], ignore_index=True)
    df_final_consolidado.to_csv(ARCHIVO_FINAL, index=False, encoding='utf-8-sig')

    print(f"\n💾 Guardado en: {ARCHIVO_FINAL}")
    print(f"   Total registros: {len(df_final_consolidado)}")
    print(f"   Total columnas:  {len(df_final_consolidado.columns)}")

    # Muestra qué columnas del cuadro se capturaron
    cols_ml = [c for c in df_final_consolidado.columns
               if c not in df_a_procesar.columns and c not in ('Titulo','Ubicacion','Descripcion_Larga')]
    print(f"\n📋 Columnas del cuadro capturadas ({len(cols_ml)}):")
    print("   " + ", ".join(cols_ml[:30]) + ("..." if len(cols_ml) > 30 else ""))

print("\n🏁 Fin del Script 2.")
