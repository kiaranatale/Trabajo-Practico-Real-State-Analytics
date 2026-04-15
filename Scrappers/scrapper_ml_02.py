import pandas as pd
import re
import os

# --- RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_ENTRADA = os.path.join(BASE_DIR, 'base_flipper_detallada_ml.csv')
ARCHIVO_SALIDA = os.path.join(BASE_DIR, 'mercadolibre_final_unificado.csv')

# --- LISTA COMPLETA DE COLUMNAS (63) ---
COLUMNAS_OBJETIVO = [
    "Precio", "Expensas", "Calle", "Altura", "Piso", "Link", "Ambientes", "Dormitorios", 
    "Baños", "Toilettes", "Estado", "Antiguedad", "Disposicion", "Orientacion", 
    "Tipo_Balcon", "Apto_Profesional", "Apto_Credito", "Tipo_Unidad", "Tipo_Operacion", 
    "Sup_Cubierta_m2", "Sup_Total_m2", "Sup_Desc_m2", "Precio_Ficha", "Expensas_Ficha", 
    "Cant_Pisos_Edificio", "Deptos_Por_Piso", "Antig_Edif", "Estado_Edif", 
    "Aire_acondicionado_individual", "Electricidad", "Losa_radiante", "Gas_natural", 
    "Agua_corriente", "Agua_caliente", "Balcón", "Terraza", "Jardín", "Patio", "Baulera", 
    "Cochera", "Muebles_de_cocina", "Lavarropas", "Lavavajillas", "Conexión_para_lavarropas", 
    "Permite_Mascotas", "Apto_Crédito", "Ascensor", "Pileta", "Piscina", "Parrilla", "SUM", 
    "Gimnasio", "Sauna", "Laundry", "Seguridad_24hs", "Vigilancia", 
    "Acceso_mov_reducida", "Pavimento", "ABL", "Smart_Amenities", 
    "Smart_Losa_Central", "Smart_Luminoso", "Smart_Balcon_Aterrazado", "Precio_m2", "Barrio"
]

# --- FUNCIONES DE LIMPIEZA ---

def solo_numeros(valor):
    if pd.isna(valor) or str(valor).strip() == "" or str(valor).lower() == "n/a": return 0
    match = re.search(r'(\d+)', str(valor))
    return int(match.group(1)) if match else 0

def limpiar_precio_expensas(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0
    v = str(valor).lower().replace('usd', '').replace('$', '').replace('ars', '').strip()
    if re.search(r'\.\d{3}', v): v = v.replace('.', '')
    v = v.replace(',', '.')
    try:
        num = float(v)
        return int(num) if num > 1000 else int(num * 1000)
    except: return 0

def es_si(valor):
    """Convierte 'Sí' o un número > 0 en 1, de lo contrario 0."""
    v = str(valor).lower().strip()
    if v == 'sí' or v == 'si': return 1
    # Si es un número (como en cocheras), si es > 0 devolvemos 1
    num = re.search(r'(\d+)', v)
    if num and int(num.group(1)) > 0: return 1
    return 0

def minar_todo(row):
    t_desc = str(row.get('Descripcion_Larga', '')).lower()
    # Normalizar columnas de la tabla de ML
    r_c = {str(k).lower().strip(): v for k, v in row.items()}
    
    d = {c: 0 for c in COLUMNAS_OBJETIVO}
    for c in ["Calle", "Altura", "Piso", "Estado", "Disposicion", "Orientacion", "Link", "Barrio"]: d[c] = "N/A"

    # --- 1. DATOS BÁSICOS Y PRECIOS ---
    d['Link'] = row.get('Link', 'N/A')
    d['Precio'] = limpiar_precio_expensas(row.get('Precio', row.get('Precio_Web', 0)))
    d['Expensas'] = limpiar_precio_expensas(r_c.get('expensas', 0))
    d['Precio_Ficha'], d['Expensas_Ficha'] = d['Precio'], d['Expensas']

    # --- 2. SUPERFICIES Y UNIDADES ---
    # Usamos r_c.get para buscar en la tabla técnica primero
    d['Sup_Total_m2'] = float(str(r_c.get('superficie total', '0')).replace(' m²', '').replace(',', '.')) if r_c.get('superficie total') else 0.0
    d['Sup_Cubierta_m2'] = float(str(r_c.get('superficie cubierta', '0')).replace(' m²', '').replace(',', '.')) if r_c.get('superficie cubierta') else 0.0
    d['Ambientes'] = solo_numeros(r_c.get('ambientes'))
    d['Dormitorios'] = solo_numeros(r_c.get('dormitorios'))
    d['Baños'] = solo_numeros(r_c.get('baños'))
    d['Antiguedad'] = solo_numeros(r_c.get('antigüedad'))

    # --- 3. TEXTOS (DISPOSICIÓN, ORIENTACIÓN, PISO) ---
    d['Orientacion'] = str(r_c.get('orientación', 'N/A')).capitalize()
    d['Disposicion'] = str(r_c.get('disposición', 'N/A')).capitalize()
    
    piso_val = r_c.get('número de piso de la unidad')
    piso_txt = re.search(r'(\d+)\s*(?:piso|er piso|do piso|to piso)', t_desc)
    d['Piso'] = str(piso_val) if pd.notnull(piso_val) else (piso_txt.group(1) if piso_txt else "PB")

    # --- 4. MAPEO MASIVO DE AMENITIES Y SERVICIOS (Prioridad Tabla) ---
    # Mapeamos nombre de tu columna -> Nombre en la imagen de ML
    mapping_binary = {
        "Patio": "patio",
        "Jardín": "jardín",
        "Cochera": "cocheras",
        "Terraza": "terraza",
        "Balcón": "balcón",
        "Parrilla": "parrilla",
        "Pileta": "pileta",
        "SUM": "salón de usos múltiples",
        "Gimnasio": "gimnasio",
        "Sauna": "sauna",
        "Laundry": "lavandería",
        "Gas_natural": "gas natural",
        "Agua_corriente": "agua corriente",
        "Electricidad": "luz",
        "Aire_acondicionado_individual": "aire acondicionado",
        "Agua_caliente": "caldera",
        "Ascensor": "ascensor",
        "Apto_Crédito": "apto crédito",
        "Permite_Mascotas": "permite mascotas",
        "Conexión_para_lavarropas": "con conexión para lavarropas",
        "Baulera": "baulera"
    }

    for col_destino, etiqueta_ml in mapping_binary.items():
        # Primero buscamos en la tabla técnica
        if es_si(r_c.get(etiqueta_ml, '')):
            d[col_destino] = 1
        # Si la tabla no lo tiene o dice No, buscamos en la descripción como fallback
        elif re.search(col_destino.lower(), t_desc):
            d[col_destino] = 1

    # --- 5. UBICACIÓN ---
    partes = str(row.get('Ubicacion', '')).split(',')
    if len(partes) >= 1:
        calle_alt = partes[0].strip()
        m_dir = re.search(r'^(.*?)\s+(\d+)$', calle_alt)
        d['Calle'] = m_dir.group(1).strip() if m_dir else calle_alt
        d['Altura'] = m_dir.group(2).strip() if m_dir else "S/N"
    if len(partes) >= 2: d['Barrio'] = partes[-2].strip()

    # --- 6. ESTADO Y KPI ---
    if re.search(r'refaccionar|reciclar|original|deterioro', t_desc): d['Estado'] = "A refaccionar"
    else: d['Estado'] = "Bueno"

    if d['Sup_Total_m2'] > 0:
        d['Precio_m2'] = round(float(d['Precio']) / d['Sup_Total_m2'], 2)

    return pd.Series(d)

# --- EJECUCIÓN ---
if __name__ == "__main__":
    df = pd.read_csv(ARCHIVO_ENTRADA, encoding='utf-8-sig')
    df_final = df.apply(minar_todo, axis=1)

    # Convertir a Enteros Int64 (excepto superficies)
    cols_int = ["Precio", "Expensas", "Ambientes", "Dormitorios", "Baños", "Antiguedad"]
    for c in cols_int:
        df_final[c] = pd.to_numeric(df_final[c], errors='coerce').fillna(0).astype('Int64')
    
    df_final.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8-sig')
    print(f"✅ ¡Proceso terminado! Patio, Jardín y Cochera mapeados desde la tabla técnica.")
