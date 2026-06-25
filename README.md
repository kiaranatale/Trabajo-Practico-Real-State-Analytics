# Trabajo Práctico: Real Estate Analytics - CABA

**Grupo:** Kiara Natale, Gonzalo Haro, Justo Celsi  
**Materia:** Analítica Descriptiva — ITBA  

---

## Índice

1. [Resumen Ejecutivo](#0-resumen-ejecutivo)
2. [Perfil del Cliente](#1-perfil-del-cliente)
3. [Contexto Económico](#2-contexto-económico)
4. [Alcance del Proyecto](#3-alcance-del-proyecto)
5. [Preguntas de Investigación](#4-preguntas-de-investigación)
6. [Hipótesis y Resultados](#5-hipótesis--resultados)
7. [KPIs Definidos](#6-kpis-definidos)
8. [Estructura del Repositorio](#7-estructura-del-repositorio)
9. [Pipeline Analítico](#8-pipeline-analítico)
10. [Análisis Avanzado](#9-análisis-avanzado)
11. [Decisiones Metodológicas](#10-decisiones-metodológicas)
12. [Conclusiones y Recomendaciones de Negocio](#11-conclusiones-y-recomendaciones-de-negocio)
13. [Limitaciones y Líneas Futuras](#12-limitaciones-y-líneas-futuras)
14. [Reflexión: Hacia la Producción](#13-reflexión-hacia-la-producción)
15. [Dashboard](#14-dashboard)
16. [Fuentes](#15-fuentes)

---

## 0. Resumen Ejecutivo

Este proyecto analiza el mercado inmobiliario de la Ciudad Autónoma de Buenos Aires (CABA) para responder una pregunta concreta de negocio: **¿dónde y cómo debería desplegar capital un fondo de inversión inmobiliaria que compite contra el bono soberano argentino en USD (~10% anual)?**

A partir de más de 8.500 publicaciones activas scrapeadas de Argenprop, MercadoLibre y Remax, y enriquecidas con datos de delitos, subte, parques y Censo 2022, construimos un pipeline analítico completo que reduce el universo a **3.140 propiedades con renta estimada confiable** y produce criterios de inversión replicables.

**Hallazgos principales:**

- La **rentabilidad bruta mediana del mercado es 6,21%** — 379 puntos básicos por debajo del bono soberano en USD. El alquiler tradicional en CABA no compite con el activo financiero de referencia sin una estrategia complementaria.
- Las dos variables que más determinan el yield son el **precio por m²** y la **superficie cubierta**: propiedades por debajo de 2.000 USD/m² y menos de 60 m² tienen rentabilidad predicha consistentemente por encima de la mediana del mercado (modelo Random Forest, R² CV = 0,731).
- La **prima del alquiler temporal es +37%** sobre el alquiler tradicional (IC 95%: +3,42 a +6,21 USD/m²/mes). En zonas turísticas (comunas 1, 3 y 13), esta reconversión es la única vía que acerca el retorno al bono.
- Las propiedades **a estrenar tienen un premium de precio del +27%** que no se recupera vía alquiler: su rentabilidad bruta es 137 pb menor que la de propiedades usadas y su payback es 4,4 años más largo.

**Recomendación central:** el fondo debería concentrarse en departamentos usados de superficie pequeña (< 60 m²) en comunas 1, 3 y 13, con precio de adquisición por debajo de 2.000 USD/m², evaluando reconversión a alquiler temporal para cerrar el gap con el bono.

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
│   ├── 05_analisis_factorial.ipynb           # Diagnóstico FA → PCA (4 componentes)
│   ├── 06_clustering.ipynb                   # Segmentación K-Means (k=4) + Ward
│   ├── 07_modelos_explicativos.ipynb         # OLS + árbol de decisión + Random Forest
│   ├── Readme Feature Engineering.md
│   ├── Readme limpieza.md
│   └── reporte_hallazgos.md
│
├── Datos2/
│   ├── processed/
│   │       ├── dataset_ventas_limpio.csv             # Output nb01
│   │       ├── dataset_alquiler_limpio.csv           # Output nb01
│   │       ├── dataset_ventas_features.csv           # Output nb02 — ventas con KPIs y features
│   │       └── dataset_alquileres_features.csv       # Output nb02 — alquileres con features
│   ├── Dataframes.py
│   ├── dataset_ventas_pca_scores.csv         # Output nb05 — ventas con 4 componentes PCA
│   ├── dataset_ventas_clusters.csv           # Output nb06 — ventas con segmentos
│   └── importancia_variables.csv             # Output nb07 — importancia RF + coefs OLS
│
├── Datos Contextuales/
│   ├── bla.geojson
│   ├── callejero.csv
│   └── datasets_contextuales.py
│
├── data_raw/
│   ├── datos_argenprop_ventas.tsv
│   ├── datos_argenprop_alquiler.tsv
│   ├── datos_mercadolibre_ventas.csv
│   ├── datos_remax_venta.csv
│   ├── datos_remax_alquiler.csv
│   ├── ml_crudo_p1.csv
│   ├── ml_crudo_p2.csv
│   ├── ml_crudo_p3.csv
│   ├── ml_crudo_p4.csv
│   ├── ml_crudo_p5.csv
│   ├── ml_crudo_p6.csv
│   └── ml_crudo_p7.csv
│
├── Scrappers/
│   ├── .keep
│   ├── scrapper_argenprop_alquiler.py
│   ├── scrapper_argenprop_venta.py
│   ├── scrapper_ml_00_consola.txt
│   ├── scrapper_ml_01.py
│   ├── scrapper_ml_02.py
│   ├── scrapper_remax_alquiler.py
│   └── scrapper_remax_ventas.py
│
└── README.md
```

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

### Decisiones de preprocesamiento

El volumen inicial de ~8.500 publicaciones se redujo a 3.140 propiedades analizables a través de tres etapas de filtrado:

**Limpieza estructural:** deduplicación por combinación de precio, superficie y dirección; exclusión de tipologías no residenciales (casas, PHs, locales); imputación de ambientes faltantes por texto de descripción. Se corrigió un bug de propagación del campo `A_estrenar` que afectaba al 60% de los registros de antigüedad — la variable se reconstruyó como binario desde el slug de URL de Argenprop.

**Geocodificación:** el callejero oficial de CABA permitió geolocalizar el 90,6% de las propiedades. El 9,4% restante no pudo asignarse a una comuna con certeza y fue excluido de los análisis espaciales.

**Filtro de confianza de renta:** cada propiedad en venta hereda la renta mediana de su celda `(Comuna, Tipología, banda_sup)` en el dataset de alquileres. Celdas con menos de 3 comparables reciben confianza `baja` y se excluyen de todos los análisis de rentabilidad, para no modelar sobre estimaciones sin respaldo empírico.

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

### 9.2 Segmentación (notebook 06)

**Objetivo:** identificar perfiles de inversión diferenciados sin imponer categorías externas.

**Decisiones metodológicas:**
- **Input:** 4 componentes PCA del notebook 05 (ortogonales, estandarizados — distancia euclidiana significativa).
- **K-Means** con 50 inicializaciones, `k-means++`. Validación independiente con clustering jerárquico Ward.
- **k = 4** — silhouette máximo (0.29) + interpretabilidad comercial.
- **Cohesión:** silhouette = 0.29 y DB = 1.10 indican solapamiento moderado — esperado y consistente con el KMO bajo del nb05.

**Segmentos identificados:**

| Cluster | N | Precio/m² | Rent. bruta | Payback | Zona riesgo | Barrio top |
|---|---|---|---|---|---|---|
| **0** | 546 (17%) | 2.321 USD/m² | 6.38% | 15.7 años | Medio | Flores |
| **1** | 1.172 (37%) | 2.000 USD/m² | 7.76% | 12.9 años | Alto | Recoleta |
| **2** | 1.259 (40%) | 3.133 USD/m² | 5.27% | 19.0 años | Bajo | Palermo |
| **3** | 163 (5%) | 2.483 USD/m² | 5.37% | 18.6 años | Medio | Villa del Parque |

**Hallazgo central:** ningún cluster cumple simultáneamente rentabilidad diferencial y escalabilidad. El Cluster 1 maximiza yield (7,76%) pero con liquidez marginal. El Cluster 2 es el único escalable pero rinde por debajo del mercado (5,27%). La inversión en CABA implica elegir entre yield y escala.

### 9.3 Modelos Explicativos (notebook 07)

**Objetivo:** cuantificar qué variables explican la rentabilidad bruta anual y con qué magnitud.

| Modelo | R² / métrica | Observaciones |
|---|---|---|
| OLS (HC3 robusto) | R²aj = 0.327 | Supuestos violados (heterocedasticidad, no normalidad) — IC válidos con HC3 |
| Árbol de decisión | R² CV = 0.92 | **Caveat:** R² inflado por discretización del target (tabla puente de renta) |
| Random Forest | R² CV = 0.731 ± 0.092 | Modelo más robusto; importancia por permutación confiable |

**Variables con mayor poder explicativo** (importancia por permutación, Random Forest):

| Variable | Importancia perm. | Interpretación |
|---|---|---|
| `Precio_m2_USD` | 0.428 | Yield cae de ~21% a ~4.5% entre 500 y 5.500 USD/m² |
| `Sup_Cubierta_m2` | 0.395 | La renta no escala con la superficie; yield colapsa por encima de 60-80 m² |
| `Tipologia_monoamb` | 0.068 | Monoambientes suman yield marginalmente |
| `Indice_amenities` | 0.024 | Efecto dispar: positivo en OLS, marginalmente negativo en PDP del RF |
| `Liquidez_oferta_comuna` | 0.012 | Comunas más activas tienen más comparables |

**Umbral accionable:** propiedades por debajo de ~2.000 USD/m² y menos de 60 m² tienen rentabilidad predicha consistentemente por encima de la mediana del mercado.

---

## 10. Decisiones Metodológicas

### Taxonomía de variables del dataset

| Categoría | Variables | Confiabilidad |
|---|---|---|
| **Observadas** | Precio_m2_USD, Sup_Cubierta_m2, Ambientes, Indice_amenities, Distancias, Tasa_delitos, Liquidez | Alta |
| **Imputadas** | Renta_estimada_mensual_USD (tabla puente), Volatilidad_Precio_m2_comuna (agregado comunal) | Media — confianza_renta documenta calidad |
| **Derivadas válidas** | Rentabilidad_bruta_anual, Precio_m2_mediano_comuna | Alta si inputs son confiables |
| **Excluidas de modelos** | Antiguedad (bug), Payback_anios (tautología), Yield_gap (derivada del target), Precio_USD (determinismo algebraico) | No usar |

### Filtros estándar del pipeline

| Constante | Valor | Razón |
|---|---|---|
| `GEO_OK_FILTER` | True | Solo propiedades geocodificadas |
| `SUPERPREMIUM_QUANTILE` | p99 | Excluye outliers extremos |
| `CONFIANZA_EXCLUIR` | 'baja' | Excluye rentas con poca base de comparables |

---

## 11. Conclusiones y Recomendaciones de Negocio

### Conclusión general

El alquiler tradicional en CABA **no compite con el bono soberano en USD como estrategia de inversión aislada**. Con una rentabilidad bruta mediana de 6,21% frente a un costo de oportunidad de ~10%, el yield gap es de aproximadamente 379 puntos básicos. Este resultado no es consecuencia de un mercado ineficiente sino de una estructura de precios que incorpora expectativas de apreciación del capital — el inversor que solo captura renta pierde contra el activo financiero.

Sin embargo, el análisis revela que existen combinaciones de activo y estrategia que permiten **acortar significativamente ese gap**, e incluso superarlo en escenarios favorables.

### Recomendaciones por orden de impacto

**1. Filtro duro de precio de adquisición: ≤ 2.000 USD/m²**  
Es la variable con mayor poder predictivo sobre el yield (importancia 0,428 en Random Forest). Por encima de ese umbral, la rentabilidad cae de forma no lineal. Este filtro descarta automáticamente el segmento premium y a estrenar — que son, precisamente, las trampas de yield del mercado.

**2. Priorizar superficie pequeña: < 60 m²**  
La renta no escala proporcionalmente con la superficie. Los departamentos chicos concentran mejor retorno por peso invertido. Monoambientes y 2 ambientes compactos son el perfil objetivo; los 3 ambientes típicos son la tipología de menor yield relativo (5,71% mediana).

**3. Evitar propiedades a estrenar para renta**  
El premium de precio (+27%) no se recupera vía alquiler. La rentabilidad bruta de propiedades nuevas es 137 pb menor que la de usadas y el payback se extiende 4,4 años. Para un fondo de renta, lo usado bien comprado domina estructuralmente.

**4. Evaluar reconversión a alquiler temporal en zonas turísticas**  
La prima del alquiler temporal es +37% sobre el tradicional (IC 95%: +3,42 a +6,21 USD/m²/mes). En comunas 1, 3 y 13, esta estrategia permite acercar el retorno al bono. La condición es que la tasa de ocupación efectiva supere el umbral de break-even, que el análisis de precios publicados no puede garantizar.

**5. Incorporar apreciación de capital como componente de retorno**  
El análisis de corte transversal no captura apreciación. Para que el retorno total supere el bono, la apreciación anual del activo debe compensar el yield gap (~3,8 pp). Históricamente el real estate en CABA ha mostrado apreciación real en dólares en horizontes largos, pero este componente está fuera del alcance del análisis presente y debe modelarse separadamente.

### Mapa de decisión por perfil

| Perfil de activo | Estrategia recomendada | Yield esperado | Observación |
|---|---|---|---|
| Usado < 60 m², < 2.000 USD/m², comunas 1/3/13 | Temporal turístico | ~9% (estimado) | Depende de ocupación efectiva |
| Usado < 60 m², < 2.000 USD/m², otras comunas | Tradicional largo plazo | ~7-8% | Perfil objetivo del fondo |
| A estrenar, cualquier zona | No recomendado para renta | ~5% | Premium de precio no recuperable |
| > 3.000 USD/m² (segmento premium) | No recomendado para renta | ~4-5% | Yield insuficiente |

---

## 12. Limitaciones y Líneas Futuras

### Limitaciones actuales

| Limitación | Impacto | Mitigación aplicada |
|---|---|---|
| `Antiguedad` no confiable como continua | No usable en modelos | Se usa `A_estrenar` binario (reconstruida) |
| Datos de corte transversal | Sin análisis de tendencias ni apreciación de capital | Documentado en scope |
| ~9-10% sin geocodificación | Excluidos de análisis espaciales | Sesgo verificado como leve |
| Confianza_renta baja en Comunas 4, 8, 9 | Rentabilidades del sur menos confiables | Filtro aplicado; advertencia documentada |
| Alquiler temporal sin tasa de ocupación | H6 validada solo como prima de precio publicado | Caveat explícito en todos los análisis |
| PCA explica 63.9% de varianza | 36.1% de información no capturada en clusters | Clusters leídos sobre variables originales |
| Target discretizado por tabla puente | R² del árbol inflado artificialmente | Se usa RF como modelo principal |

### Líneas futuras de investigación

- **Series de tiempo:** incorporar datos históricos de precios para modelar apreciación del capital y estacionalidad del alquiler temporal.
- **Tasa de ocupación efectiva:** integrar datos de plataformas de alquiler temporal (AirDNA, datos propios) para modelar el yield real del alquiler turístico, no solo el de lista.
- **Modelado de riesgo de vacancia:** estimar probabilidad de vacancia por zona y tipología para calcular rentabilidad neta ajustada por riesgo.
- **Expansión geográfica:** extender el análisis al GBA, donde el precio de entrada es menor y el yield gap respecto al bono puede ser más favorable.
- **Modelo de valorización:** construir un modelo predictivo de precio/m² para identificar propiedades subvaluadas en zonas de alta liquidez.

---

## 13. Reflexión: Hacia la Producción

El pipeline analítico actual es reproducible pero manual: requiere ejecutar los notebooks en orden, con los datasets correctos en la carpeta `/Datos2`. Llevarlo a un entorno productivo implicaría tres capas de automatización:

### Capa 1 — Actualización de datos (scraping automatizado)

Los scrapers actuales se ejecutan manualmente desde los notebooks. Para automatizar:
- **Argenprop / MercadoLibre:** los scripts de `aiohttp` + `BeautifulSoup` pueden empaquetarse como funciones y orquestarse con **Apache Airflow** o **GitHub Actions** con ejecución semanal.
- **Remax:** requiere **Playwright** (sitio renderizado con JavaScript). Podría correr en un contenedor Docker con Chromium headless, disparado por el mismo orquestador.
- Los datos crudos se depositarían en un bucket de **S3** o **Google Cloud Storage**, versionados por fecha de scraping.

### Capa 2 — Pipeline de transformación (datos procesados)

El pipeline de limpieza, geocodificación y feature engineering (notebooks 01–02) puede refactorizarse como un módulo Python con funciones puras y ejecutarse con **dbt** (si se usa un warehouse SQL) o como scripts en **Prefect/Airflow**. La tabla puente de renta se recalcularía con cada nueva ingesta.

### Capa 3 — Dashboard actualizado

El dashboard de Power BI consume CSVs estáticos. Para que se actualice automáticamente:
- **Opción A (sin infraestructura adicional):** conectar Power BI Service a un SharePoint o Google Drive donde el pipeline deposita los CSVs actualizados. Power BI refresca según calendario.
- **Opción B (más robusta):** migrar las fuentes a una base de datos en la nube (PostgreSQL en RDS, BigQuery, o Snowflake) y conectar Power BI vía conector nativo. El pipeline escribe directamente a la base.

### Consideraciones adicionales

- **Monitoreo de calidad:** agregar checks automáticos de `confianza_renta` por lote para detectar degradación del dataset de alquileres (menos publicaciones → más celdas con confianza baja).
- **Alertas de mercado:** configurar alertas cuando el yield mediano del mercado cambie más de ±50 pb respecto al período anterior, o cuando el bono soberano USD supere un umbral configurable.
- **Modelo en producción:** el Random Forest puede servirse como API REST (FastAPI + pickle del modelo) para que el fondo evalúe propiedades individuales en tiempo real antes de una oferta.

---

## 14. Dashboard

- **Dashboard interactivo en Power BI Service:** [Acceso público al Dashboard](https://app.powerbi.com/view?r=eyJrIjoiZjY0ZmRjOTItM2Q3My00YTZmLTlhMDMtY2VjMzdjYTgwNzA5IiwidCI6ImExZjUwYTk3LTIxYzAtNDlhNy1hOWQ0LWYyNDRlYmI0MmRhNyIsImMiOjR9&pageName=4bef21b19b98ae90d7c6)

---

## 15. Fuentes

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
