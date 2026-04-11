import pandas as pd
import re

# 1. CARGA
df = pd.read_csv('base_flipper_detallada_ml.csv', encoding='utf-8-sig', dtype={'Precio': str})

# 2. FUNCIÓN DE LIMPIEZA DE PRECIO (Mantenemos la lógica de enteros)
def limpiar_precio(val):
    if pd.isna(val): return None
    v = str(val).lower().replace('usd', '').replace('$', '').replace(' ', '').strip()
    v = v.replace('.0', '000') if v.endswith('.0') else v.replace('.', '')
    try:
        num = float(v.replace(',', ''))
        if num < 1000: num *= 1000
        return int(num)
    except: return None

df['Precio_Num'] = df['Precio'].apply(limpiar_precio).astype('Int64')

# 3. FUNCIÓN DE MINERÍA DE TEXTO AVANZADA
def minar_detalles_full(texto):
    t = str(texto).lower()
    d = {}

    # --- NUMÉRICOS ---
    # Metros Cuadrados
    m2 = re.search(r'(\d+)\s*(?:m2|metros|mts|mt2)', t)
    d['m2'] = int(m2.group(1)) if m2 else None

    # Ambientes Totales
    amb = re.search(r'(\d+)\s*(?:ambiente|amb)', t)
    d['Ambientes'] = int(amb.group(1)) if amb else None
    if 'monoambiente' in t: d['Ambientes'] = 1

    # Dormitorios (Habitaciones)
    dorm = re.search(r'(\d+)\s*(?:dormitorio|dorm|habitación|habitacion|cuarto)', t)
    d['Dormitorios'] = int(dorm.group(1)) if dorm else None

    # Baños
    banos = re.search(r'(\d+)\s*(?:baño|bañ)', t)
    d['Baños'] = int(banos.group(1)) if banos else 1 # Asumimos 1 si no dice nada

    # --- BINARIOS (0 o 1) - AMENITIES Y CARACTERÍSTICAS ---
    d['Tiene_Cochera'] = 1 if re.search(r'cochera|estacionamiento|garage|fijo', t) else 0
    d['Tiene_Balcon'] = 1 if re.search(r'balcón|balcon|aterrazado', t) else 0
    d['Tiene_Terraza'] = 1 if re.search(r'terraza|patio', t) else 0
    d['Tiene_Lavadero'] = 1 if re.search(r'lavadero|conexión para lavarropas', t) else 0
    
    # Smart Amenities (Requisito de la consigna)
    d['Smart_Amenities'] = 1 if re.search(r'pileta|piscina|sum|gym|gimnasio|sauna|laundry|parrilla', t) else 0
    d['Smart_Seguridad'] = 1 if re.search(r'seguridad|vigilancia|totem|monitoreo', t) else 0
    d['Smart_Luminoso'] = 1 if re.search(r'luminoso|todo luz|sol|vista abierta', t) else 0
    
    # Estado (Clave para Flipper)
    d['A_Refaccionar'] = 1 if re.search(r'refaccionar|reciclar|original|estado regular|antiguo|humedad', t) else 0

    return pd.Series(d)

print("⛏️ Minando datos profundos de la descripción...")
df_extra = df['Descripcion_Larga'].apply(minar_detalles_full)

# Unimos todo
df = pd.concat([df, df_extra], axis=1)

# 4. CONVERSIÓN DE TIPOS PARA EVITAR EL .0
cols_enteros = ['Precio_Num', 'm2', 'Ambientes', 'Dormitorios', 'Baños', 
                'Tiene_Cochera', 'Tiene_Balcon', 'Tiene_Terraza', 
                'Smart_Amenities', 'A_Refaccionar']

for col in cols_enteros:
    df[col] = df[col].astype('Int64')

# 5. KPIs Y BARRIO
df['Precio_m2'] = df['Precio_Num'] / df['m2'].astype(float)
df['Barrio'] = df['Ubicacion'].apply(lambda x: str(x).split(',')[-2].strip() if len(str(x).split(',')) >= 2 else "N/A")

# 6. GUARDAR
df_final = df.dropna(subset=['Precio_Num', 'Link']).copy()
df_final.to_csv('base_datos_flipper_pro_ml.csv', index=False, encoding='utf-8-sig')

print(f"✅ ¡Dataset Pro finalizado! Quedaron {len(df_final)} propiedades.")
print(df_final[['Precio_Num', 'Barrio', 'Dormitorios', 'Tiene_Cochera', 'A_Refaccionar']].head())
