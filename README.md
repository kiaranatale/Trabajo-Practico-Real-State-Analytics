# Trabajo-Practico-Real-State-Analytics
Realizado por: Kiara Natale, Gonzalo Haro y Justo Celsi.

*Dataset analizados*:
Se consiguieron las bases de datos de Argenprop (mediante el scrapper otorgado por la catedra con algunas modificaciones para mejorar y acelerar el acceso a los datos), Mercado Libre (mediante un scrapper generado por nosotros para podes unir todas los registros), y Remax (generando 2 scrappers diferentes para compras y alquileres).

*Seleccion del perfil*
El perfil seleccionado corresponde a un Fondo de Inversión Inmobiliaria interesado en evaluar oportunidades de compra para posterior renta. Este perfil busca maximizar el retorno de inversión comparando diferentes estrategias de explotación inmobiliaria.

# Alcance del Proyecto
Geográfico: Ciudad Autónoma de Buenos Aires (CABA), análisis desagregado por comuna y barrio.

Temporal: Datos de publicaciones activas al momento del scraping (2025). Datos históricos de delitos 2016–2024.

Tipologías: Departamentos (monoambiente, 2, 3 y 4+ ambientes). Se excluyen casas, PH y locales comerciales en el análisis principal.

Estrategias de renta: Alquiler tradicional (largo plazo) y alquiler temporal (corto plazo / turístico).

# Hipotesis 
La hipótesis general es que en la Ciudad Autónoma de Buenos Aires existen tipos de propiedades y zonas específicas que muestran una mayor rentabilidad potencial para un fondo de inversión inmobiliaria, y esperamos observar que ciertos factores —como superficie, ubicación, tipo de alquiler (tradicional vs. temporal) y presencia de amenities— se asocian con diferencias significativas en los ingresos por renta y en el tiempo de recupero de la inversión.

Algunas de las preguntas de investigación, desde los distintos niveles de análisis, son las siguientes:

Análisis descriptivo:

* ¿Qué tipos de propiedades presentan mayor rentabilidad potencial?
  
Análisis diagnóstico:

* ¿Qué características de las propiedades impactan en el ingreso por alquiler?
  
Análisis predictivo:

* ¿Qué zonas presentan mejor relación entre precio de compra e ingreso estimado?
* ¿Cuál es el tiempo estimado de recupero de la inversión según el tipo de alquiler?
  
Análisis prescriptivo:

* ¿Conviene más la renta tradicional o el alquiler temporal?
* ¿Según los pronósticos a futuro, hay algun barrio o zona en la que convenga invertir?¿Alguno en el que sea una mala idea hacerlo?

Para responder estas preguntas se construirán indicadores clave como ingreso mensual estimado, rentabilidad bruta anual, precio por metro cuadrado, superficie promedio, análisis de amenities y tiempo de recupero de la inversión. Estos indicadores permitirán identificar oportunidades y comparar distintas estrategias de inversión inmobiliaria.

Hipótesis específicas:

• H1: Las propiedades cercanas a estaciones de subte presentan mayor rentabilidad que aquellas alejadas del transporte público.

• H2: Los departamentos pequeños (monoambientes y 2 ambientes) presentan mayor rentabilidad.

• H3: La cercanía a espacios verdes incrementa el precio del m².

• H4: Los departamentos a estrenar presentan menor rentabilidad que los usados debido a su mayor precio inicial.

• H5: Las propiedades ubicadas en comunas con menor tasa de delitos presentan mayor precio por m².

# Recoleccion de datos
Al mismo tiempo, será necesario integrar bases de datos contextuales:

En primer lugar, es necesario mapear la calle y altura de las propiedades para obtener su latitud y longitud, y asi poder cruzar con datos externos que tienen referencias geograficas. Al mismo tiempo identificar a que comuna pertenece cada propiedad, para ello sera necesario el dataset de "Comunas" de la ciudad de buenos aires.Para esto vamos a necesitar Callejero csv, obtenido de buenos aires data, que contiene datos de las calles y su referencia geografica por altura, ademas de a que comuna pertenece la calle en esa altura.

Las bases contextuales para la que nos sera util el dato de la ubicacion geografica:

*Delitos de la ciudad de buenos aires, extrayendo y concatenando las bases de datos disponibles desde 2016 hasta 2024, que tienen detalle de cada robo y hurto cometido por comuna y con detalle de ubicacion geoespacial.

*Mapa de ruido diurno y nocturno ambos datasets extraidos desde buenos aires data con mediciones hechas en 2025. Es un dato relevante porque determina la calidad de vida.

*Espacios verdes publicos: nos permite evaluar cercania con espacios verdes.

*Obras inciadas: nos permite evaluar si alguna zona se está gentrificando y en el futuro valdrá más.

*Lineas de subte: nos permite evaluar la cercania con el medio de transporte, lo que le agrega valor a una propiedad

*Oferta gastronomica: nos permite evaluar la cercania con locales gastronomicos.

*Areas hospitalarias: nos permite evaluar cercania con hospitales.

Estos son solo algunos de los datasets contextuales que nos pueden ser útiles para sumar a las bases de datos inmobiliarias que ya fueron scrappeadas.

# KPIs definidos

Para responder las preguntas planteadas se definieron los siguientes indicadores clave:

• Precio por m² = Precio de la propiedad / Superficie cubierta

• Ingreso mensual estimado = Promedio de alquiler de propiedades comparables en la misma zona

• Rentabilidad bruta anual = (Ingreso mensual estimado * 12) / Precio de compra

• Tiempo de recupero de la inversión = Precio de compra / Ingreso anual estimado

• Índice de amenities = Cantidad de amenities presentes por propiedad

• Distancia a transporte público = Distancia geográfica a la estación más cercana

# Desafíos técnicos en la recolección

Durante el proceso de scraping se encontraron distintos desafíos:

• Paginación dinámica en los portales inmobiliarios
• Bloqueos por demasiadas solicitudes simultáneas
• Estructuras HTML distintas entre páginas
• Datos faltantes o inconsistentes en algunas publicaciones
• Diferentes formatos de moneda y superficie

Estos problemas fueron resueltos mediante el uso de scraping asincrónico, control de tiempos de espera, validaciones y limpieza posterior de los datos.

