# Trabajo Práctico: Real Estate Analytics - CABA
**Hecho por:** Kiara Natale, Gonzalo Haro, Justo Celsi

## 0. Perfil del Cliente

El cliente es un fondo de inversión inmobiliaria con capital propio disponible para desplegar en activos reales dentro de CABA. Su función objetivo es maximizar el retorno sobre el capital invertido a través de ingresos por renta, evaluando dos estrategias de explotación: alquiler tradicional de largo plazo y alquiler temporal turístico.

El perfil condiciona todas las decisiones analíticas del proyecto de las siguientes formas:

- Horizonte de inversión: Mediano-largo plazo (5–10 años). No busca flipping rápido sino flujo de caja sostenido con preservación de capital en dólares.
- Función objetivo: Maximizar rentabilidad bruta anual y minimizar el payback period, sujeto a un nivel de riesgo aceptable (volatilidad de ingresos, riesgo regulatorio, zona de seguridad).
- Restricción de financiamiento: Opera con capital propio. Esto implica que el costo de oportunidad relevante no es la tasa hipotecaria sino el rendimiento de activos alternativos comparables en el mercado argentino (bonos en dólares, plazo fijo UVA, etc.).

Escala: El fondo evalúa múltiples propiedades simultáneamente, por lo que necesita criterios replicables y comparables entre activos, no análisis caso por caso.

Este perfil excluye del análisis principal las dimensiones relevantes para un comprador final (calidad de vida, cercanía a colegios, hospitales) y prioriza las variables directamente vinculadas al retorno financiero: precio por m², ingreso por alquiler, payback period y riesgo por zona.

---

## 1. Definición del Contexto Económico

### Realidad del Mercado Inmobiliario Argentino

El mercado inmobiliario de Argentina opera bajo restricciones estructurales que definen fundamentalmente la lógica de inversión:

#### Dinámica Inflacionaria y Dolarización
- La persistente inflación Argentina (promedio 2021-2024: ~100% anual) ha generado una **progresiva dolarización de facto** del mercado inmobiliario de compraventa.
- A diferencia de otros mercados, los precios de publicación y los valores efectivos de cierre presentan **diferencias significativas**, especialmente en CABA.
- La brecha entre precio de publicación y valor de cierre se estima en 4,91% según el relevamiento de marzo de 2026 elaborado por UCEMA, RE/MAX Argentina y Reporte Inmobiliario, basado exclusivamente en operaciones concretadas. Este valor se aplica como descuento fijo sobre los precios de publicación en todos los cálculos de rentabilidad y payback period.
- Los inversores evalúan propiedades como **protección de valor** (hedge contra devaluación), no solo como flujo de renta.


#### Mercado de Alquiler: Dualidad Regulatoria
- **Alquiler de largo plazo (tradicional):** Regulado desde 2020 por Ley 27.551 (actualización anual según IPC). Genera retornos **moderados pero estables**.
- **Alquiler temporal/turístico:** No regulado. Retornos **superiores pero volátiles** (sensible a ciclos turísticos y regulación futura).
- Esta dualidad **crea oportunidades de arbitraje**: propiedades con características diferentes pueden ser más rentables bajo estrategias distintas.

#### Crédito Hipotecario Limitado
- La disponibilidad de crédito hipotecario en Argentina es **extremadamente limitada** (tasas > 40% anual en pesos en 2024-2025).
- Esto implica que los inversores utilizan **capital propio**, modificando la función objetivo: maximizar retorno absoluto (no relativo al crédito).
- Consecuencia: la inversión inmobiliaria compete con **activos alternativos** (bonos, dólares), no solo con otras propiedades.

#### Heterogeneidad Territorial y Relación Precio-Ingresos
- CABA concentra ingresos ~2-3× superiores al promedio nacional.
- Esta **varianza intra-territorial** genera comunas con dinámicas de precio completamente distintas.
- Zonas de ingreso alto → mayor demanda de alquiler temporal. Zonas mixtas → demanda de alquiler tradicional.

### Problema de Negocio

Un **fondo de inversión inmobiliaria** busca evaluar oportunidades de compra para posterior explotación vía renta. Su objetivo es **identificar zonas y tipologías donde la relación precio de compra / ingreso por alquiler sea favorable**, comparando estrategias (largo vs. corto plazo) y estimando tiempos de recupero de inversión.

**Restricción clave:** La decisión se toma sabiendo que el precio inicial (compra) representa principalmente una **protección de valor**, no una apuesta especulativa al crecimiento.

---

## 2. Alcance del Proyecto

### Delimitación Geográfica
- **Ciudad Autónoma de Buenos Aires (CABA)**
- Análisis desagregado por **comuna** (nivel de política urbana) y **barrio** (nivel de experiencia del residente)
- Se reconoce heterogeneidad territorial: dinámicas de inversión distintas según ubicación

### Delimitación Temporal
- **Datos de publicaciones activas:** Al momento del scraping (2025)
- **Datos contextuales históricos:** Delitos 2016-2024 (para evaluar tendencias)
- Limitación: análisis de corte transversal + series históricas cortas; no es un panel de propiedades

### Tipologías de Propiedades
- **Incluidas:** Departamentos (monoambiente, 2, 3 y 4+ ambientes)
- **Excluidas:** Casas, PH, locales comerciales (dinámicas de inversión distintas)
- Justificación: departamentos concentran inversión institucional y tienen mercado de alquiler más líquido
- Tratamiento del segmento super-premium: Dentro de los departamentos incluidos, las propiedades con precio/m² por encima del umbral que se identificará al observar la distribución empírica en el EDA se clasificarán como segmento "super-premium". Este segmento se excluye de los promedios generales y los KPIs de mercado para evitar distorsión.


### Estrategias de Explotación
1. **Alquiler tradicional (largo plazo):** Ingresos regulados, predecibles
2. **Alquiler temporal/turístico (corto plazo):** Ingresos superiores pero volátiles
3. **Objetivo:** Comparar ROI y payback period por estrategia y ubicación

---

## 3. Preguntas de Investigación por Nivel Analítico

### Nivel Descriptivo
¿Cuál es la **distribución actual** de precios, rentas y características de las propiedades en CABA?

- ¿Qué tipología de departamento (monoambiente, 2, 3, 4+ ambientes) presenta mayor volumen de oferta?
- ¿Cuál es la distribución de precios por m² según comuna?
- ¿Cuál es la distribución de rentas (largo y corto plazo) según zona?

### Nivel Diagnóstico
¿Qué **características de la propiedad y su ubicación** explican variaciones en precios y rentas?

- ¿Cómo impacta la superficie cubierta en el precio total y en el precio por m²?
- ¿Cómo impacta la proximidad a transporte público (subte) en el precio de compra y en la rentabilidad neta?
- ¿Cómo impacta la presencia de amenities (piscina, gym, seguridad 24h) en el precio y en la demanda de alquiler?
- ¿Las propiedades a estrenar comandan un precio premium? ¿Ese premium se recupera vía alquiler?
- ¿Cómo impacta la ubicación en zona de alto delito en el precio de compra y en la capacidad de rentar?

### Nivel Predictivo
¿Cuál es el **valor esperado de la renta** y el **retorno estimado** dadas las características de la propiedad?

- Dado el precio de compra, superficie, ubicación y amenities de una propiedad, ¿cuál es el ingreso mensual esperado según estrategia de alquiler (largo plazo vs. temporal)?
- ¿Cuál es el **tiempo estimado de recupero de inversión (payback period)** para una propiedad típica según zona y estrategia?
- ¿Existen **zonas emergentes** (obras iniciadas, mejoras en infraestructura) donde se espera crecimiento de demanda futura?

### Nivel Prescriptivo
¿Cuál es la **mejor estrategia de inversión** según el perfil del fondo y las oportunidades identificadas?

- **Decisión estratégica:** ¿Conviene priorizar alquiler de largo plazo (ingresos estables, baja volatilidad) o temporal (ingresos superiores, mayor riesgo)?
- **Decisión geográfica:** ¿En cuáles comunas/barrios la relación precio-renta es más favorable? ¿Dónde es riesgoso invertir?
- **Decisión tipológica:** ¿Qué tamaño de departamento (monoambiente vs. 2-3 ambientes) maximiza ROI según estrategia?
- ¿Qué oportunidades de arbitraje existen entre zonas de presencia turística vs. zonas residenciales?

---

## 4. Hipótesis Reformuladas (Causales Claras)

### H1: Accesibilidad a Transporte Público → Precio de Compra (NO → Rentabilidad)
**Formulación:** La proximidad a estaciones de subte está **capitalizada en el precio de compra**, pero no genera **rentabilidad diferencial**.

**Lógica causal:** Una propiedad cerca de subte es más demandada → precio sube. Pero como inversión, el ingreso por alquiler crece proporcionalmente al precio. Luego: rentabilidad (ingresos/precio) se mantiene similar.

**Implicación:** Comparar propiedades cercanas vs. lejanas a subte no por rentabilidad, sino por **accesibilidad para el inquilino** (¿afecta demanda? ¿duración de alquiler?).

---

### H2: Tamaño de Propiedad → Rentabilidad Diferencial
**Formulación:** Los departamentos pequeños (monoambientes y 2 ambientes) presentan **mayor rentabilidad bruta anual** que departamentos grandes (3 y 4+ ambientes).

**Lógica causal:** Propiedades pequeñas tienen menor precio absoluto pero renta casi tan alta (monoambiente vs. 2 amb. tienen demanda similar). Luego: ratio renta/precio es superior.

**Validación:** Comparar rentabilidad bruta (ingreso anual / precio compra) entre tipologías.

---

### H3: Presencia de Espacios Verdes Próximos → Precio por m²
**Formulación:** La cercanía a espacios verdes públicos se asocia con **mayor precio por m²**, independientemente de otras características.

**Lógica causal:** Los espacios verdes son un **atributo exógeno** (no generado por especulación de precios) que mejora calidad de vida → mayor demanda → mayor precio/m².

**Validación:** Usar distancia mínima a parque como variable explicativa de precio/m².

---

### H4: Condición (Estrenar vs. Usado) → Rentabilidad Ajustada
**Formulación:** Los departamentos a estrenar presentan **menor rentabilidad neta** en los primeros 5-10 años debido a su mayor precio inicial, aunque pueden generar apreciación futura.

**Lógica causal:** Propiedades nuevas comandan premium de precio (20-40%) que no se refleja en aumento de renta de alquiler. Luego, payback period es más largo.

**Validación:** Comparar precio/m², ingreso estimado y payback period entre nuevos y usados.

---

### H5: Tasa de Delitos → Precio (Relación Multicausal, Requiere Control)
**Formulación:** Zonas con menor tasa de delitos presentan **mayor precio por m²**, pero esta relación es **confundida por ingreso del vecindario, infraestructura y disponibilidad de servicios**.

**Lógica causal (reconociendo confusión):** Ingresos altos → inversión en seguridad y servicios → menos delitos → más demanda → mayor precio. No es el delito per se, sino los **factores estructurales** detrás.

**Implicación:** No usar delito como predictor directo. Usar como **variable de segmentación** (zonas de riesgo bajo, medio, alto) para evaluar si la renta compensa el riesgo.

---

### H6 (NUEVA): Estrategia de Alquiler → Retorno Diferencial
**Formulación:** El **alquiler temporal (corto plazo) genera mayor ingreso mensual** que el alquiler tradicional, pero con **mayor volatilidad y riesgo de regulación**.

**Lógica causal:** Alquiler temporal: precio/noche × ocupación esperada. Alquiler largo: precio fijo regulado. Ubicación turística vs. residencial → demanda distinta.

**Implicación:** Comparar ingresos y volatilidad por estrategia. Identificar propiedades "híbridas" que puedan cambiar de estrategia.

---

## 5. KPIs Definidos

### Indicadores de Precio
- **Precio por m²:** Precio de compra / Superficie cubierta
  - Uso: Comparabilidad entre zonas y propiedades
  
- **Precio promedio por barrio/comuna:** Agregación para comparativas
  - Uso: Identificar tendencias geográficas

### Indicadores de Ingreso
- **Ingreso mensual estimado (alquiler largo plazo):** Promedio de ofertas de alquiler similar en zona
  - Uso: Base para cálculo de rentabilidad
  
- **Ingreso mensual potencial (alquiler temporal):** Precio/noche × ocupación esperada
  - Uso: Comparar con alquiler tradicional
  

### Indicadores de Rentabilidad
- **Rentabilidad bruta anual:** (Ingreso mensual × 12) / Precio de compra
  - Uso: Comparar propiedades; identificar oportunidades
  
- **Rentabilidad neta anual:** (Ingreso mensual × 12 - Gastos anuales) / Precio de compra
  - Gastos incluyen: impuesto inmobiliario, mantenimiento (3-5% alquiler), seguros
  - Uso: Cálculo más realista

### Indicadores de Recupero
- **Payback period (años):** Precio de compra / Ingreso anual
  - Uso: Tiempo hasta recuperar inversión (sin considerar apreciación)
  
- **Payback period ajustado:** Considera amortización esperada por inflación
  - Uso: Realista en contexto argentino (inflación reduce valor real de deuda)

### Indicadores de Ubicación y Amenidades
- **Distancia a subte más cercano (km):** Georreferenciación
  - Uso: Evaluación de accesibilidad
  
- **Índice de amenities:** Cantidad y tipo de servicios (piscina, gym, seguridad 24h, etc.)
  - Uso: Control en modelos; expectativa: mayor amenity → mayor precio, pero no necesariamente mayor renta

### Indicadores de Riesgo
- **Tasa de delitos (por 10k habitantes):** Por comuna, agregado histórico 2016-2024
  - Uso: Segmentación de riesgo; no como predictor directo
  
- **Índice de volatilidad de precios:** Coeficiente de variación de precios/m² en los últimos 12 meses (si hay datos)
  - Uso: Identificar zonas inestables    (probablemente será descartada)

---

## 6. Recolección de Datos

### Bases Inmobiliarias (Obtenidas)

1. **Argenprop:** Scraping con modificaciones catedrálicas
2. **Mercado Libre:** Scraper propio para consolidación
3. **Remax:** 2 scrappers (compras y alquileres)

**Consolidación:** Base unificada con variables estandarizadas (precio, superficie, ubicación, amenities, tipo de propiedad).

### Bases Contextuales (Integración Operativa)

#### Mapeo Geográfico (Crítico)
- **Callejero CABA (Buenos Aires Data):** Mapea calle + altura → latitud/longitud → comuna
- **Operación:** Geocodificar cada propiedad (calle + altura) → obtener coordenadas y comuna
- **Desafío:** Direcciones incompletas o ambiguas; requiere validación y fuzzy matching

#### Seguridad (Relevancia: Alta)
- **Delitos CABA (2016-2024, Buenos Aires Data):** Robos y hurtos por ubicación geoespacial y comuna
- **Operación:** Agregar tasa de delitos por comuna; crear zona de riesgo bajo/medio/alto
- **Uso:** Segmentación; NO como predictor directo de renta

#### Infraestructura de Transporte (Relevancia: Alta)
- **Líneas de subte (Buenos Aires Data):** Estaciones georreferenciadas
- **Operación:** Calcular distancia mínima cada propiedad a estación de subte
- **Uso:** Validar H1 (efecto en precio, NO en rentabilidad)

#### Espacios Verdes (Relevancia: Media-Alta)
- **Parques y espacios públicos (Buenos Aires Data):** Polígonos georreferenciados
- **Operación:** Calcular distancia mínima a parque; crear dummy "cercanía a verde"
- **Uso:** Validar H3 (efecto en precio/m²)

#### Calidad de Vida (Relevancia: Media, pero Validar)
- **Ruido diurno/nocturno (Buenos Aires Data, 2025):** Mediciones en decibeles por zona
- **Nota anterior (crítica):** Ruido no es buen predictor de valor (Villa Lugano silenciosa pero barato; Av. Libertador ruidoso pero caro)
- **Recomendación:** Incluir pero **no priorizar** como variable explicativa; usar para análisis descriptivo

#### Gentrificación/Cambio Urbano (Relevancia: Media)
- **Obras iniciadas:** Identificar zonas en transformación
- **Uso:** Análisis descriptivo; predicción cualitativa de zonas emergentes
- **Limitación:** Datos puede ser incompletos; usar con cautela
  
### Variables Excluidas del Análisis Principal
- **Oferta gastronómica:** Excluida. Presenta múltiple causalidad y es más reflejo del nivel socioeconómico del barrio que causa de valor. Irrelevante para la función objetivo del fondo inversor.
- **Áreas hospitalarias:** Excluida. Relevante para comprador final buscando calidad de vida, no para un fondo que optimiza rentabilidad. Su inclusión respondería a un perfil de cliente distinto al definido.


---

## 7. Desafíos Técnicos y Soluciones

### Recolección (Scraping)
| Desafío | Solución |
|---------|----------|
| Paginación dinámica | Scraping asincrónico (aiohttp, Scrapy) |
| Bloqueos por rate limiting | Control de tiempos de espera; rotación de user-agents |
| Estructuras HTML heterogéneas | Parsers flexibles; validación de cada fuente |
| Datos faltantes o inconsistentes | Validación en captura; imputación posterior si necesaria |
| Formatos distintos (moneda, superficie) | Estandarización post-scraping |

### Consolidación
- **Deduplicación:** Misma propiedad en múltiples portales → mantener único registro
- **Validación geográfica:** Direcciones mal formateadas → geocodificación con fuzzy matching
- **Valores atípicos:** El umbral de separación del segmento super-premium se determina observando la distribución empírica de precio/m² en el EDA, identificando el punto de quiebre natural en la cola derecha de la distribución. No se predefine un criterio fijo. Las propiedades sobre ese umbral no se eliminan sino que se segmentan para análisis separado

### Integración de Datos Contextuales
- **Joins geográficos:** Ubicar cada propiedad en comuna; calcular distancias a puntos de interés
- **Manejo de datos faltantes contextuales:** Si no hay datos delitos en una zona → imputar con promedio comunal

### Fuentes de información
Reporte Inmobiliario, Abril 2026 - https://www.reporteinmobiliario.com/article5803-precio-real-de-cierre-por-m%C2%B2-%E2%80%93-marzo-2026
---
