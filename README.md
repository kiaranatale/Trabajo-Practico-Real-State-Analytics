# Trabajo Práctico: Real Estate Analytics - CABA

**Grupo:** Kiara Natale, Gonzalo Haro, Justo Celsi  
**Materia:** Analítica Descriptiva — ITBA  

---

## Índice

1. [Perfil del Cliente](#1-perfil-del-cliente)
2. [Contexto Económico](#2-contexto-económico)
3. [Alcance del Proyecto](#3-alcance-del-proyecto)
4. [Preguntas de Investigación](#4-preguntas-de-investigación)
5. [Hipótesis y Resultados](#5-hipótesis--resultados)
6. [KPIs Definidos](#6-kpis-definidos)
7. [Estructura del Repositorio](#7-estructura-del-repositorio)
8. [Pipeline Analítico](#8-pipeline-analítico)
9. [Análisis Avanzado](#9-análisis-avanzado)
10. [Decisiones Metodológicas](#10-decisiones-metodológicas)
11. [Limitaciones](#11-limitaciones)
12. [Próximos Pasos](#12-próximos-pasos)
13. [Fuentes](#13-fuentes)

---

## 1. Perfil del Cliente

Fondo de inversión inmobiliaria con capital propio disponible para desplegar en activos reales dentro de CABA. Su función objetivo es maximizar el retorno sobre el capital invertido a través de ingresos por renta, evaluando dos estrategias: **alquiler tradicional de largo plazo** y **alquiler temporal turístico**.

- **Horizonte de inversión:** mediano-largo plazo (5–10 años).
- **Función objetivo:** maximizar rentabilidad bruta anual y minimizar payback period, sujeto a riesgo aceptable.
- **Restricción de financiamiento:** opera con capital propio. El costo de oportunidad relevante es el rendimiento de bonos soberanos argentinos en USD (~10% anual, rango histórico 2024-2025: 8-12%), no una tasa hipotecaria.
- **Escala:** el fondo evalúa múltiples propiedades simultáneamente — necesita criterios replicables y comparables entre activos.

---

## 2. Contexto Económico

- **Dolarización de facto:** precios de compraventa nominados en USD con una brecha de cierre de **4,91%** respecto al precio de publicación (UCEMA/RE/MAX/Reporte Inmobiliario, marzo 2026). Todos los KPIs usan `Precio_ajustado_USD = Precio_publicación × 0.9509`.
- **Dualidad regulatoria del alquiler:** largo plazo regulado por Ley 27.551 vs. temporal no regulado (mayor yield, mayor volatilidad).
- **Crédito hipotecario inaccesible:** el fondo compite con activos financieros en USD, no con financiamiento inmobiliario.
- **Heterogeneidad territorial:** las 15 comunas de CABA presentan dinámicas de precio y rentabilidad radicalmente distintas.

---

## 3. Alcance del Proyecto

- **Geografía:** Ciudad Autónoma de Buenos Aires (CABA), desagregada por comuna.
- **Período:** datos de publicaciones activas al momento del scraping (2025). Análisis de corte transversal.
- **Tipologías:** departamentos (monoambiente, 2, 3 y 4+ ambientes). Excluidas casas, PHs y locales.
- **Segmento super-premium:** propiedades con `Precio_m2_USD > p99` se excluyen de los promedios y KPIs generales.

---

## 4. Preguntas de Investigación

| Nivel | Pregunta |
|---|---|
| **Descriptivo** | ¿Cuál es la distribución actual de precios, rentas y características por tipología y comuna? |
| **Diagnóstico** | ¿Qué características de la propiedad y su ubicación explican variaciones en precios y rentas? |
| **Predictivo** | ¿Cuál es el ingreso mensual esperado y el payback period según características de la propiedad? |
| **Prescriptivo** | ¿En qué comunas y tipologías conviene invertir? ¿Qué estrategia de renta maximiza el ROI? |

---

## 5. Hipótesis & Resultados

| # | Hipótesis | Resultado | Hallazgo clave |
|---|---|---|---|
| **H1** | Subte capitalizado en precio, no en rentabilidad | **Refutada** | El subte no discrimina ni precio ni rentabilidad — la red es suficientemente densa para eliminar variabilidad |
| **H2** | Monoambientes tienen mayor rentabilidad bruta | **Refutada** | Patrón en U invertida: monoamb (6,20%) ≈ 4+A (6,51%) > 3A (6,36%) > 2A (5,71%). Los 2A son la trampa de yield |
| **H3** | Cercanía a parques eleva el precio/m² | **Refutada (dirección invertida)** | Los parques más grandes están en comunas de menor precio — variable confundida con zonificación socioeconómica |
| **H4** | Propiedades a estrenar tienen menor rentabilidad | **Validada** | Premium de precio +27%, payback +4,4 años más largo, rentabilidad −137 pb respecto a usados |
| **H5** | Zonas de mayor delito tienen mayor rentabilidad | **Validada** | El mercado compensa parcialmente: riesgo alto rinde +73 pb sobre bajo; zona media es la peor combinación |
| **H6** | Alquiler temporal genera mayor ingreso/m² | **Validada con caveats** | Prima del +37% en renta/m² publicada (IC 95%: +3,42 a +6,21 USD/m²/mes). Sin tasa de ocupación efectiva |

> **Advertencia metodológica:** la calidad de la renta estimada (`confianza_renta`) no es uniforme por comuna. Las Comunas 4, 8 y 9 tienen mayoría de rentas con confianza baja por escasez de comparables. Las conclusiones de rentabilidad en esas comunas deben tomarse con cautela.

---

## 6. KPIs Definidos

| KPI | Fórmula | Uso |
|---|---|---|
| `Precio_m2_USD` | Precio_publicación / Sup_cubierta | Comparabilidad entre zonas |
| `Precio_ajustado_USD` | Precio × 0.9509 | Base para cálculos de retorno |
| `Rentabilidad_bruta_anual` | (Renta_mensual × 12) / Precio_ajustado | KPI central de yield |
| `Rentabilidad_neta_anual` | (Renta × 12 − ABL − Mantenimiento − 1 mes vacancia) / Precio_ajustado | Retorno efectivo estimado |
| `Payback_anios` | Precio_ajustado / Renta_anual | Tiempo de recupero de inversión |
| `Yield_gap_vs_bonos` | Rentabilidad_bruta − 10% | Diferencial vs. costo de oportunidad del fondo |
| `Indice_amenities` | Suma de binarios de servicios presentes | Control de calidad del activo |
| `Tasa_delitos_comuna` | Delitos acumulados 2017-2024 / Población Censo 2022 | Segmentación de riesgo (bajo/medio/alto) |
| `Liquidez_oferta_comuna` | Publicaciones activas / Población comunal | Escalabilidad del fondo por zona |
| `confianza_renta` | alta / media / baja según nº de comparables | Robustez de los KPIs de rentabilidad |

---

## 7. Estructura del Repositorio

```
Trabajo-Practico-Real-State-Analytics/
│
├── Notebooks/
│   ├── 01_limpieza_ventas.ipynb              # Limpieza y auditoría del dataset de ventas
│   ├── 01_limpieza_alquileres.ipynb          # Limpieza y auditoría del dataset de alquileres
│   ├── 02_feature_engineering.ipynb          # Geocodificación, KPIs, variables contextuales
│   ├── 03_eda_visualizaciones.ipynb          # EDA completo con Plotly — mapas, correlaciones
│   ├── 04_hipotesis.ipynb                    # Validación formal de H1–H6 (tests estadísticos)
│   ├── 05_analisis_factorial.ipynb           # Diagnóstico FA → PCA (4 componentes) ★
│   ├── 06_clustering.ipynb                   # Segmentación K-Means (k=4) + Ward ★
│   └── 07_modelos_explicativos.ipynb         # OLS + árbol de decisión + Random Forest ★
│
├── Datos2/
│   ├── datos_argenprop_ventas.tsv
│   ├── datos_argenprop_alquiler.tsv
│   ├── datos_mercadolibre_ventas.csv
│   ├── datos_remax_venta.csv
│   ├── datos_remax_alquiler.csv
│   ├── dataset_ventas_limpio.csv             # Output nb01
│   ├── dataset_alquiler_limpio.csv           # Output nb01
│   ├── dataset_ventas_features.csv           # Output nb02 — ventas con KPIs y features
│   ├── dataset_alquileres_features.csv       # Output nb02 — alquileres con features
│   ├── dataset_ventas_pca_scores.csv         # Output nb05 — ventas con 4 componentes PCA ★
│   ├── dataset_ventas_clusters.csv           # Output nb06 — ventas con segmentos ★
│   └── importancia_variables.csv             # Output nb07 — importancia RF + coefs OLS ★
│
├── Datos Contextuales/
│   ├── callejero.csv
│   └── datasets_contextuales.py
│
├── Scrappers/
│
└── README.md
```

`★` = nuevo en la Entrega 2

---

## 8. Pipeline Analítico

```
Scraping (Argenprop · MercadoLibre · Remax)
        ↓
01_limpieza  →  dataset_ventas_limpio.csv
                dataset_alquiler_limpio.csv
        ↓
02_feature_engineering  →  Geocodificación (callejero CABA)
                            Distancias a subte y parques
                            Tabla puente renta + confianza_renta
                            KPIs: rentabilidad, payback, yield_gap
                            dataset_ventas_features.csv
        ↓
03_eda_visualizaciones  →  Distribuciones, mapas por comuna,
                            matriz de correlaciones,
                            geografía precio vs. rentabilidad
        ↓
04_hipotesis  →  Tests formales H1–H6
                 Reporte de hallazgos estadísticos
        ↓
05_analisis_factorial  →  Diagnóstico FA: KMO = 0.42 → FA descartado
                           PCA sobre 9 variables → 4 componentes (63.9% varianza)
                           dataset_ventas_pca_scores.csv
        ↓
06_clustering  →  K-Means k=4 sobre 4 componentes PCA
                  Validación Ward — silhouette = 0.29
                  Perfiles comerciales de segmentos
                  dataset_ventas_clusters.csv
        ↓
07_modelos_explicativos  →  OLS con HC3 (R²aj = 0.327)
                             Árbol de decisión (caveat: target discretizado)
                             Random Forest — R² CV = 0.731 ± 0.092
                             importancia_variables.csv
```

---

## 9. Análisis Avanzado

### 9.1 Reducción de Dimensionalidad (notebook 05)

**Objetivo:** reducir el espacio de 9 variables candidatas e identificar estructura latente antes del clustering.

**Pipeline metodológico:**

**Paso 1 — Diagnóstico FA:**
Se evaluó primero si el Análisis Factorial era viable. El resultado fue negativo:
- Bartlett rechaza H₀ (existe alguna correlación) — pero es un umbral mínimo con n grande.
- **KMO global = 0.42** — por debajo del umbral mínimo de 0.50. 8 de 9 variables tienen KMO individual < 0.50.
- **Decisión: FA descartado.** El KMO bajo indica que las correlaciones parciales entre variables son tan grandes como las correlaciones simples — cada variable mantiene mayoritariamente su varianza específica, sin compartir varianza con factores latentes comunes. Este resultado *es en sí mismo un hallazgo*: el mercado inmobiliario de CABA opera en dimensiones mayormente independientes, sin constructos latentes claros.

**Paso 2 — PCA como reductor agnóstico:**
- Estandarización de las 9 variables seleccionadas.
- **N = 4 componentes** — criterio de Kaiser (autovalor > 1) + codo del scree + umbral ≥ 60% varianza acumulada.
- **Varianza explicada: 63.9%** (PC1: 21.0%, PC2: 17.8%, PC3: 13.5%, PC4: 11.6%).

**Interpretación de componentes (por loadings):**
| Componente | Interpretación | Variables dominantes |
|---|---|---|
| **PC1 — Valor de mercado** | 21.0% varianza | Precio/m² (+0.890), amenities (+0.538) ↔ rentabilidad (−) |
| **PC2 — Accesibilidad urbana** | 17.8% varianza | Distancias subte/parque ↔ liquidez |
| **PC3 — Riesgo contextual** | 13.5% varianza | Volatilidad + delitos ↔ centralidad |
| **PC4 — Tamaño** | 11.6% varianza | Superficie (loading 0.907) — dimensión ortogonal independiente |

**Nota sobre multicolinealidad:** el VIF calculado sobre las variables originales confirma que la colinealidad es moderada (ninguna supera VIF = 10), consistente con el KMO bajo — el PCA resuelve más curse of dimensionality que multicolinealidad severa.

### 9.2 Segmentación (notebook 06)

**Objetivo:** identificar perfiles de inversión diferenciados sin imponer categorías externas.

**Decisiones metodológicas:**
- **Input:** 4 componentes PCA del notebook 05 (ortogonales, estandarizados — distancia euclidiana significativa).
- **K-Means** con 50 inicializaciones, `k-means++`. Validación independiente con clustering jerárquico Ward.
- **k = 4** — silhouette máximo (0.29) + interpretabilidad comercial. Davies-Bouldin mínimo en k=7 pero la diferencia es marginal (1.039 vs 1.103) y k=7 fragmenta el mercado en segmentos no accionables.
- **Cohesión:** silhouette = 0.29 y DB = 1.10 indican solapamiento moderado — esperado y consistente con el KMO bajo del nb05. Los clusters capturan tendencias centrales diferenciadas, no segmentos estancos.

**Segmentos identificados:**

| Cluster | N | Precio/m² | Rent. bruta | Payback | Zona riesgo | Barrio top |
|---|---|---|---|---|---|---|
| **0** | 546 (17%) | 2.321 USD/m² | 6.38% | 15.7 años | Medio | Flores |
| **1** | 1.172 (37%) | 2.000 USD/m² | 7.76% | 12.9 años | Alto | Recoleta |
| **2** | 1.259 (40%) | 3.133 USD/m² | 5.27% | 19.0 años | Bajo | Palermo |
| **3** | 163 (5%) | 2.483 USD/m² | 5.37% | 18.6 años | Medio | Villa del Parque |

**Hallazgo central — accionabilidad:**

Ningún cluster cumple simultáneamente las dos condiciones de accionabilidad (rentabilidad diferencial + escalabilidad). Este resultado no es un artefacto del análisis sino una conclusión sustantiva sobre el mercado:

- **La rentabilidad bruta mediana del mercado es 6.21%** — muy por debajo del bono soberano USD (~10%). El alquiler tradicional en CABA no compite con el activo financiero de referencia en términos de yield bruto.
- **Tensión operativa:** el Cluster 1 maximiza rentabilidad (7.76%) pero con liquidez marginal y zona de riesgo alto. El Cluster 2 es el único escalable (liquidez sobre mediana) pero rinde por debajo del mercado (5.27%).
- **Implicación estratégica:** la inversión inmobiliaria en CABA solo se justifica si se incorporan otros componentes de retorno — apreciación del capital, reducción de volatilidad de portafolio, o reconversión a alquiler temporal (H6 validó una prima de ~37% sobre el alquiler tradicional).

**Conexión con hipótesis validadas:** el diferencial entre Cluster 1 y Cluster 2 (+155 bps) confirma H5 (compensación de riesgo). La ausencia de un cluster subte-céntrico es consistente con H1 refutada.

### 9.3 Modelos Explicativos (notebook 07)

**Objetivo:** cuantificar qué variables explican la rentabilidad bruta anual y con qué magnitud.

**Modelos:**

| Modelo | R² / métrica | Observaciones |
|---|---|---|
| OLS (HC3 robusto) | R²aj = 0.327 | Supuestos violados (heterocedasticidad, no normalidad) — IC válidos con HC3 |
| Árbol de decisión | R² CV = 0.92 | **Caveat:** R² inflado por discretización del target (tabla puente de renta) |
| Random Forest | R² CV = 0.731 ± 0.092 | Modelo más robusto; importancia por permutación confiable |

> **Caveat metodológico — árbol de decisión:** el R² CV del árbol (0.92) no refleja capacidad predictiva real. `Rentabilidad_bruta_anual` se calcula como `Renta_estimada × 12 / Precio_ajustado`, donde la renta proviene de la tabla puente del nb02 — todas las propiedades en la misma celda `(Comuna, Tipología, banda_sup)` reciben la misma renta mediana. Esto reduce drásticamente los valores únicos del target y permite que el árbol "memorice" los clusters de renta sin aprender relaciones reales. El Random Forest con `min_samples_leaf=10` es más robusto ante este efecto.

**Variables con mayor poder explicativo** (importancia por permutación, Random Forest):

| Variable | Importancia perm. | Coef. OLS (std) | p-valor | Interpretación |
|---|---|---|---|---|
| `Precio_m2_USD` | 0.428 | −0.034 | < 0.001 | Efecto negativo no lineal: yield cae de ~21% a ~4.5% entre 500 y 5.500 USD/m² |
| `Sup_Cubierta_m2` | 0.395 | −0.011 | < 0.001 | La renta no escala con la superficie; yield colapsa por debajo de 60-80 m² |
| `Tipologia_monoamb` | 0.068 | +0.008 | < 0.001 | Monoambientes suman yield marginalmente — refuerza patrón en U de H2 |
| `Indice_amenities` | 0.024 | +0.005 | < 0.001 | Efecto dispar: positivo en OLS, marginalmente negativo en PDP del RF |
| `Liquidez_oferta_comuna` | 0.012 | +0.009 | < 0.001 | Positivo en OLS — comunas más activas tienen más comparables |

**Umbral accionable:** propiedades por debajo de ~2.000 USD/m² y menos de 60 m² tienen rentabilidad predicha por encima de la mediana del mercado (6.21%).

---

## 10. Decisiones Metodológicas

### Taxonomía de variables del dataset

Para el modelado de la Entrega 2 se clasificaron todas las variables según su origen:

| Categoría | Variables | Confiabilidad |
|---|---|---|
| **Observadas** | Precio_m2_USD, Sup_Cubierta_m2, Ambientes, Indice_amenities, Distancias, Tasa_delitos, Liquidez | Alta |
| **Imputadas** | Renta_estimada_mensual_USD (tabla puente), Volatilidad_Precio_m2_comuna (agregado comunal) | Media — confianza_renta documenta calidad |
| **Derivadas válidas** | Rentabilidad_bruta_anual, Precio_m2_mediano_comuna | Alta si inputs son confiables |
| **Excluidas de modelos** | Antiguedad (bug), Payback_anios (tautología), Yield_gap (derivada del target), Precio_USD (determinismo algebraico) | No usar |

### Bug de imputación de Antigüedad (identificado en Entrega 1)

El proceso de limpieza identificaba correctamente "a estrenar" en el campo `Estado` pero descartaba la columna antes de propagar la información a `Antiguedad`. La imputación posterior concentró artificialmente >60% de los valores en ~40 años (mediana). **Solución:** se recuperaron 153 propiedades adicionales parseando el patrón `a-estrenar` en el slug de URL de Argenprop. Solo `A_estrenar` (binario reconstruido) se usa en los modelos.

### Tabla puente de renta estimada

Cada propiedad en venta hereda la renta mediana de la celda `(Comuna, Tipología, banda_sup)` del dataset de alquileres. La columna `confianza_renta` clasifica la calidad de cada estimación. Se aplica como filtro en todos los análisis de rentabilidad (`confianza_renta ≠ 'baja'`).

### Filtros estándar del pipeline (aplicados en nb03–nb07)

| Constante | Valor | Razón |
|---|---|---|
| `GEO_OK_FILTER` | True | Solo propiedades geocodificadas |
| `SUPERPREMIUM_QUANTILE` | p99 | Excluye outliers extremos |
| `CONFIANZA_EXCLUIR` | 'baja' | Excluye rentas con poca base de comparables |

---

## 11. Limitaciones

| Limitación | Impacto | Mitigación |
|---|---|---|
| `Antiguedad` no confiable como continua | No usable en modelos | Se usa `A_estrenar` binario (reconstruida) |
| Datos de corte transversal | Sin análisis de tendencias ni apreciación de capital | Documentado en scope |
| ~9-10% sin geocodificación | Excluidos de análisis espaciales | Sesgo verificado como leve |
| Confianza_renta baja en Comunas 4, 8, 9 | Rentabilidades del sur menos confiables | Filtro aplicado; advertencia documentada |
| Alquiler temporal sin tasa de ocupación | H6 validada solo como prima de precio publicado | Caveat explícito |
| PCA explica 63.9% de varianza | 36.1% de información no capturada en clusters | Clusters leídos sobre variables originales (medianas), no solo sobre componentes |
| Target discretizado por tabla puente | R² del árbol inflado artificialmente | Caveat metodológico documentado en nb07; se usa RF como modelo principal |
| Argenprop TSV vacíos | Menor cobertura en dataset de ventas | Remax y ML cubren el mercado |

---

## 12. Próximos Pasos

- **Dashboard en Power BI:** construcción sobre OneLake con Shape Map de comunas (GeoJSON), visualización de segmentos, KPIs filtrados por tipología/estrategia, e importancia de variables del RF.
- **Enriquecimiento con datos de ocupación Airbnb:** necesario para estimar H6 más allá del precio publicado.
- **Scraping adicional en Comunas 4, 8 y 9:** para mejorar la confianza de la renta estimada en el sur de CABA.

---

## 13. Fuentes

| Fuente | Uso |
|---|---|
| Argenprop (scraping) | Precios de venta y alquiler |
| MercadoLibre (scraping) | Precios de venta |
| Remax (scraping) | Precios de venta y alquiler |
| [Callejero CABA — BA Data](https://data.buenosaires.gob.ar/dataset/calles) | Geocodificación |
| [Delitos CABA 2017-2024 — BA Data](https://data.buenosaires.gob.ar/dataset/delitos) | Tasa de delitos comunal |
| [Estaciones de subte — BA Data](https://data.buenosaires.gob.ar/dataset/subte-estaciones) | Distancia a subte |
| [Espacios verdes — BA Data](https://data.buenosaires.gob.ar/dataset/espacios-verdes) | Distancia a parques |
| [Censo 2022 — INDEC](https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-41-165) | Normalización de delitos y liquidez |
| [Reporte Inmobiliario / UCEMA / RE\|MAX (marzo 2026)](https://www.reporteinmobiliario.com) | Factor de ajuste precio de cierre (4,91%) |
