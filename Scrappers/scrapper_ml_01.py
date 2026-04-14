import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import glob
import os
import re

# --- CONFIGURACIÓN DE RUTAS AUTOMÁTICA ---
# Esto hace que el script busque la carpeta data_raw al lado del archivo .py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_ENTRADA = os.path.join(BASE_DIR, "data_raw")
ARCHIVO_FINAL = os.path.join(BASE_DIR, "base_flipper_detallada_ml.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

def extraer_detalles_propiedad(url):
    try:
        if "click1." in url: return None
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        datos = {}
        filas = soup.find_all(class_=re.compile(r"ui-pdp-specs__table-row|ui-pdp-table__row"))
        for fila in filas:
            label = fila.find(["th", "div"], class_=re.compile(r"label|column-label"))
            value = fila.find(["td", "div"], class_=re.compile(r"value|column-value"))
            if label and value:
                datos[label.get_text().strip()] = value.get_text().strip()
        desc_div = soup.find(class_=re.compile(r"ui-pdp-description__content"))
        datos['Descripcion_Larga'] = desc_div.get_text(separator=" ").strip() if desc_div else "N/A"
        return datos
    except Exception:
        return None

# --- PASO 1: LEER TODOS LOS ARCHIVOS ---
print(f"📂 Buscando archivos en: {CARPETA_ENTRADA}")

# Cambié el patrón de búsqueda para que acepte tanto "datos_mercadolibre" como "ml_crudo"
archivos_crudos = glob.glob(os.path.join(CARPETA_ENTRADA, "*.csv"))

if not archivos_crudos:
    print(f"⚠️ No se encontraron archivos .csv en {CARPETA_ENTRADA}")
    # Diagnóstico: Ver qué hay en la carpeta
    if os.path.exists(CARPETA_ENTRADA):
        print(f"Contenido actual de la carpeta: {os.listdir(CARPETA_ENTRADA)}")
    else:
        print(f"❌ La carpeta '{CARPETA_ENTRADA}' ni siquiera existe.")
else:
    print(f"✅ Se encontraron {len(archivos_crudos)} archivos.")
    lista_dfs = []
    for f in archivos_crudos:
        try:
            # Intentamos leer. Si el JS usó ';' como separador, lo aclaramos
            df_temp = pd.read_csv(f, sep=';', encoding='utf-8-sig')
            lista_dfs.append(df_temp)
        except Exception as e:
            print(f"❌ Error leyendo {f}: {e}")

    if lista_dfs:
        df_nuevo = pd.concat(lista_dfs).drop_duplicates(subset=['Link'])
        
        # --- PASO 2: CARGA INCREMENTAL ---
        if os.path.exists(ARCHIVO_FINAL):
            df_existente = pd.read_csv(ARCHIVO_FINAL, encoding='utf-8-sig')
            df_a_procesar = df_nuevo[~df_nuevo['Link'].isin(df_existente['Link'])].copy()
        else:
            df_existente = pd.DataFrame()
            df_a_procesar = df_nuevo.copy()

        print(f"🔍 Propiedades nuevas para procesar: {len(df_a_procesar)}")

        # --- PASO 3: SCRAPEO ---
        if not df_a_procesar.empty:
            lista_detalles = []
            for i, url in enumerate(df_a_procesar['Link']):
                detalles = extraer_detalles_propiedad(url)
                lista_detalles.append(detalles if detalles else {})
                print(f"🏠 [{i+1}/{len(df_a_procesar)}] Procesando: {url[:40]}...")
                time.sleep(random.uniform(3, 5))
            
            df_detalles = pd.DataFrame(lista_detalles)
            df_nuevos_completos = pd.concat([df_a_procesar.reset_index(drop=True), df_detalles], axis=1)
            df_final_consolidado = pd.concat([df_existente, df_nuevos_completos], ignore_index=True)
            df_final_consolidado.to_csv(ARCHIVO_FINAL, index=False, encoding='utf-8-sig')
            print(f"💾 Guardado total: {len(df_final_consolidado)}")
        else:
            print("☕ Todo está al día.")

print("🏁 Fin.")
