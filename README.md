# Trabajo-Practico-Real-State-Analytics
Realizado por: Kiara Natale, Gonzalo Haro y Justo Celsi.

*Dataset analizados*:
Se consiguieron las bases de datos de Argenprop (mediante el scrapper otorgado por la catedra con algunas modificaciones para mejorar y acelerar el acceso a los datos), Income Airbnb (mediante un scrapper generado por nosotros para podes unir todas las bases de datos que proveen), y Remax (generando 2 scrappers diferentes para compras y alquileres, y luego uniendo las bases de datos).

*Seleccion del perfil*
El perfil seleccionado corresponde a un Fondo de Inversión Inmobiliaria interesado en evaluar oportunidades de compra para posterior renta, tanto mediante alquiler tradicional como alquiler temporal tipo Airbnb. Este perfil busca maximizar el retorno de inversión comparando diferentes estrategias de explotación inmobiliaria.

La hipótesis general es que en la Ciudad Autónoma de Buenos Aires existen tipologías de propiedades y zonas específicas que muestran una mayor rentabilidad potencial para un fondo de inversión inmobiliaria, y esperamos observar que ciertos factores —como superficie, ubicación, tipo de alquiler (tradicional vs. temporal) y presencia de amenities— se asocian con diferencias significativas en los ingresos por renta y en el tiempo de recupero de la inversión.

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

Estos son solo algunos de los datasets contextuales que nos pueden ser útiles.

