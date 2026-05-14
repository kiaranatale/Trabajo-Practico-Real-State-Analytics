---
## Reporte de Hallazgos Estadísticos
### Inteligencia de Mercado Inmobiliario · CABA
---

### 1. El subte no es un driver ni de precio ni de rentabilidad

H1 postulaba que la cercanía al subte está capitalizada en el precio pero no genera rentabilidad diferencial. Los tests apuntan a una conclusión más fuerte que la teoría original: el subte directamente **no discrimina** ninguna de las dos variables en CABA.

- *Precio_m2_USD vs Distancia_subte_km:* ρ = 0,004 (Spearman), p = 0,79 — no rechazamos H0.
- *Rentabilidad_bruta_anual vs Distancia_subte_km:* ρ = −0,049, p = 0,006 — rechazo formal de H0, pero el tamaño de efecto es **despreciable** (|ρ| < 0,1, explica menos del 0,3% de la varianza). El rechazo es artefacto del n grande (3.140 observaciones).

*Consecuencia para el negocio:* la rentabilidad bruta es esencialmente independiente de la distancia al subte. La explicación más plausible es que la red de subte en CABA tiene cobertura suficientemente densa como para que casi toda propiedad esté dentro de 1,5 km de una estación — la variable pierde poder discriminante. **El fondo no debería usar cercanía al subte como criterio de selección**, ni para pagar premium ni para descontar precio. La decisión debe basarse en otros drivers.

---

### 2. La rentabilidad por tipología sigue un patrón en U invertida — H2 se refuta

H2 anticipaba una "escalera descendente" donde los departamentos más pequeños rendirían más. **El test la refuta**: el patrón observado es no monotónico y con los extremos arriba de los intermedios.

- Medianas de rentabilidad bruta por tipología: monoamb **6,20%** · 2A **5,71%** · 3A **6,36%** · 4+A **6,51%**.
- Kruskal-Wallis: H = 40,6, p = 8e-9 — rechazo de H0 (al menos una difiere).
- Post-hoc Mann-Whitney con corrección Holm: monoamb difiere significativamente de 2A; 2A difiere de 3A y 4+A; **monoamb es indistinguible de 3A y 4+A**, y 3A es indistinguible de 4+A.
- Tukey HSD confirma el mismo patrón: la diferencia es contra 2A y monoamb (el más alto), no entre tipologías chicas vs grandes.

*Consecuencia para el negocio:* el segmento 2A es la **trampa de yield** del mercado, mientras que monoambientes y 4+A rinden parecido por arriba. Esto sugiere que monoamb y 4+A capturan dos nichos distintos con pricing power propio (renta turística para chicos, alquiler premium familiar para grandes), mientras que el 2A queda en una zona "commodity" sin pricing power diferencial. Para el fondo, **diversificar en 2A es la peor estrategia de yield**; concentrarse en los extremos (4+A o monoamb según objetivo) ofrece mejor retorno medio.

---

### 3. La cercanía a parques no se traduce en mayor precio

H3 anticipaba que la cercanía a espacios verdes elevaría el precio/m². El test rechaza la hipótesis nula pero **en dirección opuesta** a la teoría.

- *Precio_m2_USD vs Distancia_parque_km:* ρ = 0,034, p = 0,043 — rechazo formal de H0.
- Medianas: cerca de parque (≤ 0,5 km) **2.317 USD/m²** vs lejos (> 1,5 km) **2.500 USD/m²**.
- El signo es **positivo**: más distancia se asocia con MÁS precio, no menos. Mann-Whitney y T-Student para la comparación cerca vs lejos no rechazan H0 (p = 0,056 y p = 0,17 respectivamente).

*Consecuencia para el negocio:* H3 se refuta no solo en magnitud sino también en dirección. La explicación geográfica es clara: los parques más grandes de CABA (Chacabuco, Patricios, Avellaneda) están en comunas medias/bajas, no en el corredor norte premium. La variable está confundida con zonificación socioeconómica. **El fondo no debe pagar premium por cercanía a parques** — en CABA esa característica está correlacionada con zonas de menor precio/m², no mayor.

---

### 4. Las propiedades a estrenar son una trampa de yield — H4 validada

**Hallazgo metodológico crítico:** durante el análisis se identificó un bug en el paso de limpieza del trabajo (`01_limpieza_ventas.ipynb`, líneas 751-861). El proceso detectaba correctamente "a estrenar" en el campo de texto `Estado`, pero descartaba la columna intermedia antes de propagar esa información a `Antiguedad`. La imputación posterior rellenó los NaN con la mediana por tipo de unidad, **enterrando todos los a-estrenar reales en el bucket de 40 años**. El primer análisis arrojaba apenas n=6 a-estrenar y resultaba estadísticamente no concluyente.

**Recuperación:** parseando el patrón `a-estrenar` en el campo `Link` (slug de URL de Argenprop) se rescatan **153 propiedades adicionales**, todas con `Antiguedad = 40` (la mediana de imputación), lo que confirma empíricamente el origen del bug. El universo corregido pasa a **n = 159 a-estrenar vs 3.297 usados**.

Con el universo corregido, los tres componentes de H4 quedan **contundentemente validados** (p < 1e-17 en todos los tests, rank-biserial r ≈ 0,41 — efecto grande):

- *Precio/m² mediano:* **3.083 USD/m²** (a estrenar) vs **2.427 USD/m²** (usado) → premium de **+27%**.
- *Payback mediano:* **20,3 años** (a estrenar) vs **15,9 años** (usado) → +4,4 años, **+28%**.
- *Rentabilidad bruta mediana:* **4,93%** (a estrenar) vs **6,30%** (usado) → −137 pb, **−22% relativo**.

*Consecuencia para el negocio:* las propiedades a estrenar son inferiores para una estrategia de renta pura. El premium de precio de ~27% no se traslada proporcionalmente a la renta, alargando el payback más de 4 años. **Para el fondo orientado a yield, el segmento usado es estructuralmente superior**. Las a-estrenar solo se justifican si se espera apreciación de capital diferencial (no testeada en este TP por falta de serie histórica) o si se prioriza menor costo de mantenimiento inicial.

---

### 5. El mercado compensa parcialmente el riesgo de zona — H5 validada

H5 plantea que las zonas de mayor delito deberían mostrar mayor rentabilidad. Los tests confirman la dirección, pero con un matiz importante.

- Medianas de rentabilidad bruta por zona: **alto 6,82%** · **bajo 6,09%** · **medio 5,57%**.
- Kruskal-Wallis: H = 105,2, p = 1e-23 — rechazo contundente.
- Post-hoc Mann-Whitney con Holm: **las tres comparaciones rechazan H0** (bajo vs medio, bajo vs alto, medio vs alto).
- *Tasa_delitos_comuna vs Precio_m2_USD:* ρ = −0,33, p < 1e-89 — efecto moderado, dirección negativa esperada.
- *Tasa_delitos_comuna vs Rentabilidad_bruta_anual:* ρ = 0,14, p < 1e-14 — efecto débil pero positivo y significativo.

El patrón es **no lineal**: la zona alta sí compensa con +73 puntos básicos sobre la baja, pero la zona media queda **por debajo** de ambos extremos. La explicación plausible es que las zonas de "riesgo medio" son barrios intermedios sin la prima del riesgo alto ni la solidez de los barrios bajos.

*Consecuencia para el negocio:* el riesgo de zona se compensa parcialmente en yield, pero la prima es modesta (~0,7 pp) y **ninguna zona supera el costo de oportunidad del bono soberano en USD** (10% anual). La zona de alto riesgo solo es justificable si se combina con alta liquidez de oferta para permitir escala. La zona de "riesgo medio" es la peor combinación absoluta: ni seguridad ni rentabilidad. Tasa_delitos queda documentada como variable asociada pero, siguiendo la advertencia del README original, no debe usarse como predictor causal — está confundida con ingreso del barrio y oferta de servicios.

---

### 6. El alquiler temporal cobra una prima sustantiva sobre el tradicional — H6 validada con caveats

H6 fue rescatable a partir de la detección automática de avisos temporales mediante el patrón `alquiler-temporal` en las URLs del dataset de alquileres. Se identificaron **128 propiedades temporales vs 2.950 tradicionales**.

- *Renta_m2_USD mediana:* **temporal 16,77 USD/m²/mes** vs **tradicional 12,21 USD/m²/mes** → prima del **+37%**.
- Mann-Whitney: U = 285.990, p = 5e-23, **rank-biserial r = 0,52 (efecto grande)** — el rechazo no es solo significancia por n alto.
- IC 95% bootstrap del diferencial de medianas: **+3,42 a +6,21 USD/m²/mes**, robusto y lejos del cero.
- Sensibilidad en Comuna 14 (Palermo, zona turística): n temporal 38 vs n tradicional 390, medianas 17,91 vs 14,22, p = 0,0003 — el patrón **se replica** al controlar por zona.

*Consecuencia para el negocio (con caveats activos):* la prima de precio publicado es real y grande, pero la decisión de inversión "temporal vs tradicional" requiere modelar variables no disponibles en el dataset: tasa de ocupación efectiva, costos de amueblamiento y rotación, comisión de plataforma, y riesgo regulatorio (CABA ya tuvo intentos legislativos en 2023 para regular el segmento). Para una propiedad de 50 m² la prima bruta es de ~228 USD/mes, pero si la ocupación del temporal cae al 60% la prima neta se reduce sustancialmente o se invierte. **H6 queda validada como prima de precio publicado**; la prima de ingreso efectivo queda pendiente de un estudio adicional con datos de ocupación.

---

### 7. Amenities y liquidez son los factores más correlacionados con precio (lectura del EDA)

Más allá de las hipótesis formales del README, dos relaciones emergieron como las más fuertes en la matriz de correlación de Spearman del EDA. Estas correlaciones se reportan a nivel descriptivo y **no están sujetas a la metodología inferencial formal** (corrección Holm, supuestos de tests) que sí aplicamos a H1-H6.

- *Indice_amenities vs Precio_m2_USD:* ρ ≈ 0,31. Cada amenity adicional se asocia con un escalón de precio/m² más alto, con medianas que van de ~2.200 USD/m² (sin amenities) a ~4.000 USD/m² (8 amenities).
- *Liquidez_oferta_comuna vs Precio_m2_USD:* ρ ≈ 0,30. Las comunas con más publicaciones por habitante concentran los precios más altos.

*Consecuencia para el negocio:* los amenities son el factor de diferenciación de precio más claro del dataset, pero también elevan las expensas — su impacto neto en rentabilidad debe modelarse específicamente en la etapa de modelado. La liquidez comunal confirma que las zonas premium son también las más activas en oferta: escalables para el fondo pero con menor yield.

---

### 8. La geografía de precio y rentabilidad son casi inversas (lectura del EDA)

El hallazgo más visualmente contundente del EDA es la inversión espacial entre precio y rentabilidad. El corredor norte (Palermo, Recoleta, Belgrano) concentra los precios más altos pero las rentabilidades más bajas. El sur y oeste (comunas 4, 8, 9) muestran el patrón opuesto.

*Consecuencia para el negocio:* no existe una zona simultáneamente premium en precio y en rentabilidad. El fondo debe elegir explícitamente entre dos estrategias: invertir en zonas premium con menor yield pero mayor liquidez y menor riesgo de vacancia, o invertir en zonas de mayor yield con menor liquidez y mayor exposición al riesgo. La matriz liquidez-rentabilidad por comuna construida en el EDA es la herramienta de priorización más directamente accionable para esta decisión.

---

### Advertencia metodológica transversal

El cruce **confianza_renta × Comuna** arroja χ² = 1.517 con **V de Cramér = 0,468 (asociación fuerte)**. Esto significa que la calidad de la renta estimada (insumo central de todos los KPIs de rentabilidad) **no está distribuida uniformemente por comuna**. Las Comunas 8, 9 y 4 (sur de CABA) tienen casi todas sus rentas estimadas con confianza baja por falta de comparables suficientes en el dataset de alquileres. Las Comunas 13, 14 y 1 son las más confiables.

*Implicación para el reporte:* las conclusiones sobre rentabilidad (H2, H4, H5) son sólidas para el corredor norte y centro pero deben tomarse con cautela en el sur de CABA, donde la tabla puente tiene poca base de comparables. Recomendamos que cualquier recomendación de inversión del fondo en Comunas 4, 8 o 9 vaya acompañada de un estudio adicional de mercado de alquileres en esa zona específica.

---

### Limitaciones relevantes para etapas posteriores

- *Antigüedad* no es utilizable como variable continua en modelos predictivos debido al bug de imputación identificado: más del 60% de los valores quedaron concentrados artificialmente alrededor de los 40 años. Solo `A_estrenar_fix` (binario, reconstruido vía URL) puede usarse con confianza.
- El *análisis temporal de precios* queda fuera de alcance: el dataset es un *snapshot* del scraping y no hay fecha de publicación por aviso. Sin variabilidad temporal no se puede testear evolución.
- *Zonas emergentes / obras iniciadas* y *apreciación futura del activo*: requieren series históricas o datos de licencias que no están en el dataset.
- El *9-10% de propiedades sin geocodificación* queda excluido de todos los análisis espaciales. Su distribución por tipología y precio no es aleatoria y podría introducir un sesgo leve en los análisis comunales.
- *Calidad de vida, hospitales y colegios*: excluidos por perfil del cliente (fondo de inversión, no comprador final), tal como se definió en la sección 1 del README.
