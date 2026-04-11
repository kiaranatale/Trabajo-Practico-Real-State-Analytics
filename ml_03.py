import pandas as pd
import re
import os

# --- 1. CONFIGURACIÓN DE COLUMNAS ---
COLUMNAS_OBJETIVO = [
    "Precio", "Expensas", "Calle", "Altura", "Piso", "Link", "Ambientes", "Dormitorios", 
    "Baños", "Toilettes", "Estado", "Antiguedad", "Disposicion", "Orientacion", 
    "Tipo_Balcon", "Apto_Profesional", "Apto_Credito", "Tipo_Unidad", "Tipo_Operacion", 
    "Sup_Cubierta_m2", "Sup_Total_m2", "Sup_Descubierta_m2", "Precio_Ficha", "Expensas_Ficha", 
    "Cant_Pisos_Edificio", "Deptos_Por_Piso", "Antiguedad_Edificio", "Estado_Edificio", 
    "Aire_acondicionado_individual", "Electricidad", "Losa_radiante", "Gas_natural", 
    "Agua_corriente", "Agua_caliente", "Balcón", "Terraza", "Jardín", "Patio", "Baulera", 
    "Cochera", "Muebles_de_cocina", "Lavarropas", "Lavavajillas", "Conexión_para_lavarropas", 
    "Permite_Mascotas", "Apto_Crédito", "Ascensor", "Pileta", "Piscina", "Parrilla", "SUM", 
    "Gimnasio", "Sauna", "Laundry", "Seguridad_24hs", "Vigilancia", 
    "Acceso_para_personas_con_movilidad_reducida", "Pavimento", "ABL", "Smart_Amenities", 
    "Smart_Losa_Central", "Smart_Luminoso", "Smart_Balcon_Aterrazado", "Precio_m2", "Barrio"
]

# --- 2. CARGA DE DATOS ---
ARCHIVO_ENTRADA = 'base_flipper_detallada_ml.csv'
if not os.path.exists(ARCHIVO_ENTRADA):
    print(f"❌ Error: No se encuentra {ARCHIVO_ENTRADA}")
    exit()

df = pd.read_csv(ARCHIVO_ENTRADA, encoding='utf-8-sig')

# --- 3. FUNCIONES DE SEGURIDAD ---

def safe_int(valor):
    """Convierte a entero de forma segura, evitando errores de texto vacío."""
    if not valor: return 0
    clean_val = re.sub(r'[^\d]', '', str(valor))
    return int(clean_val) if clean_val.isdigit() else 0

def limpiar_precio_flipper(val):
    if pd.isna(val): return 0
    v = str(val).lower().replace('usd', '').replace('$', '').replace(' ', '').strip()
    v = v.replace('.0', '000') if v.endswith('.0') else v.replace('.', '')
    num = safe_int(v)
    return num if num > 1000 else num * 1000

def minar_todo(row):
    t = str(row['Descripcion_Larga']).lower()
    tit = str(row['Titulo']).lower()
    d = {c: 0 for c in COLUMNAS_OBJETIVO}
    
    # --- DIRECCIÓN Y BARRIO ---
    partes_ubi = str(row['Ubicacion']).split(',')
    dir_full = partes_ubi[0].strip()
    match_dir = re.search(r'^(.*?)\s+(\d+)$', dir_full)
    d['Calle'] = match_dir.group(1).strip() if match_dir else dir_full
    d['Altura'] = match_dir.group(2).strip() if match_dir else "S/N"
    if len(partes_ubi) >= 2:
        d['Barrio'] = partes_ubi[-2].strip()

    # --- PISO ---
    piso_match = re.search(r'(\d+)\s*(?:piso|er piso|do piso|to piso)', t)
    d['Piso'] = piso_match.group(1) if piso_match else "PB"

    # --- EXPENSAS (CORREGIDO) ---
    exp_match = re.search(r'expensas\s*(?:\$|ars)?\s*([\d.]+)', t)
    if exp_match:
        val_exp = exp_match.group(1).replace('.', '')
        d['Expensas'] = int(val_exp) if val_exp.isdigit() else 0
    d['Expensas_Ficha'] = d['Expensas']

    # --- METROS CUADRADOS ---
    m2_match = re.search(r'(\d+)\s*(?:m2|metros|mts|mt2)', t)
    d['Sup_Total_m2'] = int(m2_match.group(1)) if m2_match and m2_match.group(1).isdigit() else 0
    d['Sup_Cubierta_m2'] = d['Sup_Total_m2']

    # --- AMBIENTES, DORMITORIOS Y BAÑOS ---
    amb = re.search(r'(\d+)\s*(?:ambiente|amb)', t + " " + tit)
    d['Ambientes'] = int(amb.group(1)) if amb and amb.group(1).isdigit() else 1
    if 'monoambiente' in t or 'monoambiente' in tit: d['Ambientes'] = 1

    dorm = re.search(r'(\d+)\s*(?:dormitorio|dorm|habitación|habitacion)', t + " " + tit)
    d['Dormitorios'] = int(dorm.group(1)) if dorm and dorm.group(1).isdigit() else (d['Ambientes'] - 1 if d['Ambientes'] > 1 else 0)

    banos = re.search(r'(\d+)\s*(?:baño|bañ)', t)
    d['Baños'] = int(banos.group(1)) if banos and banos.group(1).isdigit() else 1
    
    d['Toilettes'] = 1 if re.search(r'toilette|toilete', t) else 0

    # --- ESTADO ---
    if re.search(r'refaccionar|reciclar|original|deterioro|malo', t):
        d['Estado'] = "A refaccionar"
    elif re.search(r'impecable|excelente|estrenar|nuevo|reciclado', t):
        d['Estado'] = "Excelente"
    else:
        d['Estado'] = "Bueno"

    # --- AMENITIES BINARIOS ---
    search_map = {
        "Balcón": r"balcón|balcon", "Terraza": r"terraza", "Patio": r"patio",
        "Cochera": r"cochera|garage|estacionamiento", "Parrilla": r"parrilla",
        "Pileta": r"pileta|piscina", "SUM": r"sum|usos múltiples",
        "Gimnasio": r"gym|gimnasio", "Laundry": r"laundry|lavadero",
        "Ascensor": r"ascensor", "Apto_Credito": r"apto crédito|apto credito"
    }
    for col, regex in search_map.items():
        if re.search(regex, t): d[col] = 1

    # --- PRECIOS Y LINKS ---
    d['Precio'] = limpiar_precio_flipper(row['Precio'])
    d['Precio_Ficha'] = d['Precio']
    d['Link'] = row['Link']

    # --- KPI ---
    if d['Sup_Total_m2'] > 0 and d['Precio']:
        d['Precio_m2'] = round(d['Precio'] / d['Sup_Total_m2'], 2)

    return pd.Series(d)

# --- 4. PROCESAMIENTO ---
print("⛏️ Iniciando minería segura de descripciones...")
df_final = df.apply(minar_todo, axis=1)

# Asegurar tipos de datos Int64 para evitar el .0
cols_int = ["Precio", "Expensas", "Ambientes", "Dormitorios", "Baños", "Sup_Total_m2"]
for col in cols_int:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0).astype('Int64')

# --- 5. GUARDAR ---
OUTPUT = 'mercadolibre_final_unificado.csv'
df_final.to_csv(OUTPUT, index=False, encoding='utf-8-sig')

print(f"✅ Proceso terminado sin errores. Dataset generado: {OUTPUT}")
print(df_final[["Precio", "Barrio", "Estado", "Precio_m2"]].head())
