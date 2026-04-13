# Trabajo Práctico — Real State Analytics
**Realizado por:** Kiara Natale, Gonzalo Haro y Justo Celsi

---

## 1. Descripción de los Datasets

### Datasets Inmobiliarios (fuentes principales)

| Portal | Tipo | Método de extracción | Link |
|--------|------|----------------------|------|
| **Argenprop** | Compra y alquiler (tradicional) | Scrapper provisto por la cátedra con modificaciones propias | [argenprop.com](https://www.argenprop.com) |
| **Mercado Libre Inmuebles** | Compra y alquiler (tradicional y temporal) | Scrapper propio para unificar registros paginados | [inmuebles.mercadolibre.com.ar](https://inmuebles.mercadolibre.com.ar) |
| **Remax** | Compra y alquiler | Dos scrappers independientes (uno por modalidad) | [remax.com.ar](https://www.remax.com.ar) |

**Preferencia indicada:** Se priorizan los datos de Argenprop por ser los más completos y estructurados. Mercado Libre es la fuente secundaria por su volumen de publicaciones de alquiler temporal, clave para calcular el ingreso estimado por renta corta.

### Datasets Contextuales (fuentes de enriquecimiento geoespacial)

| Dataset | Fuente | Link | Uso previsto |
|---------|--------|------|--------------|
| Callejero CABA | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Geolocalización de propiedades (calle + altura → lat/lon) e identificación de Comuna |
| Comunas CABA (polígonos) | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Asignación geográfica de cada propiedad a su comuna |
| Delitos 2016–2024 | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Índice de seguridad por zona (H5) |
| Mapa de ruido diurno y nocturno (2025) | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Calidad de vida del entorno |
| Espacios verdes públicos | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Proximidad a parques (H3) |
| Líneas de subte (estaciones) | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Distancia a transporte público (H1) |
| Obras iniciadas | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Detección de procesos de gentrificación |
| Oferta gastronómica | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Indicador de dinamismo comercial del barrio |
| Áreas hospitalarias | Buenos Aires Data | [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar) | Proximidad a centros de salud |

---

## 2. Contexto y Situación de Negocio

### Problemática

El mercado inmobiliario de la Ciudad Autónoma de Buenos Aires (CABA) presenta una amplia heterogeneidad en cuanto a precios, características edilicias y rentabilidades potenciales. Para un inversor institucional, identificar a simple vista qué tipo de propiedad, en qué zona y con qué estrategia de explotación maximiza el retorno no es tarea trivial: la oferta es masiva, los datos están dispersos en múltiples portales y las variables que determinan el valor de renta son múltiples y correlacionadas.

### Interlocutor: Fondo de Inversión Inmobiliaria

El perfil seleccionado corresponde a un **Fondo de Inversión Inmobiliaria** interesado en adquirir propiedades en CABA para su posterior renta. El fondo no habita las propiedades: las compra como activo generador de flujo de caja, por lo que su criterio de decisión es puramente financiero. Las métricas que le importan son:

- **Rentabilidad bruta anual** (qué porcentaje del capital invertido recupera por año vía alquiler)
- **Tiempo de recupero de la inversión** (en cuántos años el ingreso acumulado iguala el precio de compra)
- **Estabilidad y tendencia del precio por m²** en la zona (para estimar plusvalía futura)

El fondo evalúa dos estrategias de explotación alternativas: **renta tradicional** (contratos de largo plazo en pesos) y **alquiler temporal** (Airbnb-style, en dólares), y necesita datos que permitan comparar ambas en términos de ingreso mensual estimado y riesgo operativo.

El alcance geográfico es **CABA completo**, con análisis desagregado por **comuna y barrio**.

---

## 3. Preguntas Clave según los 4 Niveles de Análisis

### Análisis Descriptivo
- ¿Cuál es la distribución de precios de venta y alquiler por tipo de propiedad (monoambiente, 2, 3 y 4+ ambientes)?
- ¿Qué tipos de propiedades presentan mayor rentabilidad potencial?
- ¿Cuál es el precio promedio por m² según barrio/comuna?
- ¿Qué amenities son más frecuentes en propiedades de alta rentabilidad?

### Análisis Diagnóstico
- ¿Qué características de las propiedades impactan más en el ingreso por alquiler (superficie, antigüedad, piso, amenities)?
- ¿Existe correlación entre cercanía al subte y precio por m²?
- ¿Las propiedades a estrenar tienen menor rentabilidad que los usados debido a su mayor precio inicial?
- ¿Cómo se relaciona el nivel de ruido o criminalidad de una zona con el precio de venta?

### Análisis Predictivo
- ¿Qué zonas presentan la mejor relación entre precio de compra e ingreso estimado?
- ¿Cuál es el tiempo estimado de recupero de la inversión según tipo de alquiler (tradicional vs. temporal)?
- ¿Es posible predecir el precio de alquiler de una propiedad a partir de sus características observables?
- ¿Qué barrios presentan signos de gentrificación (aumento de obras iniciadas, incremento de precio por m²) que podrían anticipar una suba de valor?

### Análisis Prescriptivo
- ¿Conviene más la renta tradicional o el alquiler temporal para maximizar el retorno?
- ¿En qué barrios o comunas debería concentrar sus compras el fondo para optimizar la rentabilidad ajustada por riesgo?
- ¿Hay zonas en las que la inversión sea desaconsejable (alta criminalidad + baja rentabilidad + precios en caída)?

---

## 4. Hipótesis y Alcance

### Hipótesis General
En la Ciudad Autónoma de Buenos Aires existen tipos de propiedades y zonas específicas que muestran una mayor rentabilidad potencial para un fondo de inversión inmobiliaria. Se espera observar que factores como la superficie, la ubicación, el tipo de alquiler (tradicional vs. temporal) y la presencia de amenities se asocian con diferencias significativas en los ingresos por renta y en el tiempo de recupero de la inversión.

### Hipótesis Específicas

| # | Hipótesis | Variable de validación |
|---|-----------|------------------------|
| H1 | Las propiedades cercanas a estaciones de subte presentan mayor rentabilidad que las alejadas del transporte público. | Distancia geoespacial a estación de subte más cercana |
| H2 | Los departamentos pequeños (monoambientes y 2 ambientes) presentan mayor rentabilidad bruta que los grandes. | Rentabilidad bruta anual por cantidad de ambientes |
| H3 | La cercanía a espacios verdes incrementa el precio del m². | Distancia al espacio verde más cercano vs. precio/m² |
| H4 | Las propiedades a estrenar presentan menor rentabilidad que las usadas debido a su mayor precio inicial. | Comparación rentabilidad bruta: estrenar vs. usado |
| H5 | Las propiedades ubicadas en comunas con menor tasa de delitos presentan mayor precio por m². | Índice de delitos por comuna vs. precio promedio/m² |

### Alcance del Proyecto

- **Geográfico:** Ciudad Autónoma de Buenos Aires (CABA), análisis desagregado por comuna y barrio.
- **Temporal:** Datos de publicaciones activas al momento del scraping (2025). Datos históricos de delitos 2016–2024.
- **Tipologías:** Departamentos (monoambiente, 2, 3 y 4+ ambientes). Se excluyen casas, PH y locales comerciales en el análisis principal.
- **Estrategias de renta:** Alquiler tradicional (largo plazo) y alquiler temporal (corto plazo / turístico).

### Hoja de Ruta Analítica

| Semana / Fase | Tarea |
|---------------|-------|
| Fase 1 (actual) | Definición de negocio, KPIs, hipótesis y scraping de datos crudos |
| Fase 2 | Limpieza, normalización, geolocalización y cruce con fuentes externas |
| Fase 3 | Análisis exploratorio (EDA): distribuciones, correlaciones, mapas de calor geoespaciales |
| Fase 4 | Modelos predictivos: regresión de precios de alquiler, clustering de zonas por perfil inversor |
| Fase 5 | Análisis prescriptivo: ranking de oportunidades, simulación de escenarios de renta |
| Fase 6 | Dashboard interactivo y presentación final de resultados |

---

## 5. Objetivo Principal del Análisis

El objetivo principal es **identificar las propiedades y zonas de CABA con mayor potencial de rentabilidad para un fondo de inversión inmobiliaria**, comparando la estrategia de renta tradicional versus alquiler temporal, y considerando variables contextuales (transporte, seguridad, espacios verdes, ruido y dinámica urbana) que afectan el valor de los activos.

Como resultado concreto, el análisis debe producir un **ranking de oportunidades de inversión** —desagregado por barrio, tipología y estrategia de renta— que le permita al fondo tomar decisiones de compra basadas en datos y no en intuición.

---

## KPIs Definidos

| Indicador | Fórmula | Interpretación |
|-----------|---------|----------------|
| **Precio por m²** | Precio de venta / Superficie cubierta | Permite comparar propiedades de distinto tamaño |
| **Ingreso mensual estimado** | Promedio de alquiler de propiedades comparables en la misma zona | Proxy del flujo de caja mensual |
| **Rentabilidad bruta anual** | (Ingreso mensual estimado × 12) / Precio de compra | Porcentaje del capital recuperado por año vía renta |
| **Tiempo de recupero** | Precio de compra / Ingreso anual estimado | Años necesarios para recuperar la inversión vía alquiler |
| **Índice de amenities** | Cantidad de amenities presentes por propiedad | Proxy de calidad edilicia y atractivo para inquilinos |
| **Distancia a transporte público** | Distancia geoespacial a la estación de subte más cercana (km) | Variable de accesibilidad urbana |

---

## Recolección de Datos: Proceso y Desafíos Técnicos

### Fuentes y Metodología

Se extrajeron datos de tres portales inmobiliarios mediante web scraping en Python:

- **Argenprop:** Se utilizó el scrapper provisto por la cátedra con modificaciones para mejorar la velocidad de acceso y la completitud de los campos extraídos.
- **Mercado Libre:** Se desarrolló un scrapper propio capaz de consolidar múltiples páginas de resultados en un único DataFrame maestro.
- **Remax:** Se construyeron dos scrappers independientes —uno para propiedades en venta y otro para alquileres— dada la diferencia estructural entre ambas secciones del sitio.

Los DataFrames resultantes capturan variables de distinto tipo: precio (numérico), cantidad de ambientes (ordinal), presencia de amenities (dicotómico), descripción de la publicación (textual), entre otros.

### Desafíos Encontrados y Soluciones

| Desafío | Solución adoptada |
|---------|-------------------|
| Paginación dinámica en portales | Scraping asincrónico con control de estado de página |
| Bloqueos por exceso de solicitudes | Tiempos de espera aleatorios (rate limiting) entre requests |
| Estructuras HTML distintas entre páginas | Selectores CSS flexibles y validación de campos por publicación |
| Datos faltantes o inconsistentes | Pipeline de limpieza y validación post-scraping |
| Diferentes formatos de moneda y superficie | Normalización a USD y m² en etapa de preprocesamiento |

---

## Estructura del Repositorio

```
/
├── data/
│   └── raw/                  # DataFrames crudos post-scraping (CSV)
├── notebooks/
│   ├── 01_scraping_argenprop.ipynb
│   ├── 02_scraping_mercadolibre.ipynb
│   └── 03_scraping_remax.ipynb
└── README.md
```
