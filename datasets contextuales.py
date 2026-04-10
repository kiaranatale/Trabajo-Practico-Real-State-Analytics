import numpy as np
import pandas as pd

import requests
#obtener datos de tipo de cambio

def get_bcra_exchange_rate(start_date='2003-01-01', end_date=None):
    if end_date is None:
        end_date = pd.to_datetime('today').strftime('%Y-%m-%d')
    
    print("To access the BCRA API, you generally need an API token.")
    print("As a free and easy alternative for 'Un request' without authentication, you might consider external APIs like 'DolarApi' or 'DolarSi' or scraping.")
    print("For direct BCRA data, you need to register on their website (https://www.bcra.gob.ar/Pdfs/Institucional/API_BCRA.pdf) to get an API token.")
    print("Once you have a token, you can use a structure similar to the commented-out code above.")
    
    # For demonstration, let's create a dummy DataFrame as a placeholder.
    print("Generating a dummy DataFrame for demonstration purposes.")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    # Simulate a rising trend for the dollar over time
    exchange_rates = 100 + np.arange(len(dates)) * 0.1 + np.random.rand(len(dates)) * 5
    
    df_exchange_rate = pd.DataFrame({
        'fecha': dates,
        'tipo_cambio_usd_ars': exchange_rates
    })
    
    return df_exchange_rate

# Call the function to get the exchange rate DataFrame
df_tipo_cambio = get_bcra_exchange_rate()
print("Head of the exchange rate DataFrame:")
print(df_tipo_cambio.head())
print("Info of the exchange rate DataFrame:")
print(df_tipo_cambio.info())

#Links

#Calles

calles = 'https://data.buenosaires.gob.ar/dataset/calles/resource/juqdkmgo-301-resource/download/callejero.csv'

#Delitos
linkcrimen2024 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/49f58c2e-21d7-4766-84e0-4bb753d28478/download/delitos-2024.csv'
linkcrimen2023 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/dbec0c29-1ada-40df-b13c-75cf3013ca42/download/delitos-2023.csv'
linkcrimen2022 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/3fbc3808-14c7-4559-8ba5-f68e919fee40/download/delitos-2022.csv'
linkcrimen2021 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/3a691e3e-6df9-412b-a300-6c611733c2c2/download/delitos-2021.csv'
linkcrimen2020 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/3f5fe778-bc8c-48ef-96fe-99aa62943152/download/delitos-2020.csv'
linkcrimen2019 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/51ba3181-fabe-4b5f-8cd4-6dfcb24b0d67/download/delitos-2019.csv'
linkcrimen2018 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/d4c82cef-3783-4da1-9e47-02df3ebba9e2/download/delitos-2018.csv'
linkcrimen2017 = 'https://data.buenosaires.gob.ar/dataset/delitos/resource/97ff15b0-fbd5-4064-8856-48798f8347e9/download/delitos-2017.csv'
linkcrimen2016 = ''

#Ruido diurno y nocturno
linkruidonoc = 'https://data.buenosaires.gob.ar/dataset/mapa-ruido/resource/b9566f33-6837-471a-ad79-441d900ba525/download/medicion_de_ruido_nocturno.csv'
linkruidodia = 'https://data.buenosaires.gob.ar/dataset/mapa-ruido/resource/4911251e-a614-4526-b062-d3d2fd557475/download/medicion_de_ruido_diurno.csv'

#Obras
linkobrasiniciadas = 'https://data.buenosaires.gob.ar/dataset/obras-iniciadas/resource/b1a162c7-f180-4420-a9e0-230d064931f2/download/obras_iniciadas.csv'

#Lineas de Subte
linksubte = 'https://data.buenosaires.gob.ar/dataset/subte-estaciones/resource/juqdkmgo-1994-resource/download/estaciones_de_subte.csv'

#Gastronomia 
linkgastronomia = 'https://data.buenosaires.gob.ar/dataset/oferta-establecimientos-gastronomicos/resource/e66613ef-aaf4-44aa-b89c-638c431fef0e/download/oferta_gastronomica.csv'

#Espacios verdes
linkeverdes = 'https://data.buenosaires.gob.ar/dataset/espacios-verdes/resource/df878bd5-5759-4af3-badc-2a4c1ae0ebf8/download/esapacio_verde_publico.csv'

#Areas hospitalarias
linkhospitales = 'https://data.buenosaires.gob.ar/dataset/areas-hospitalarias/resource/juqdkmgo-101-resource/download/areas_programaticas.csv'

d2024 = pd.read_csv(linkcrimen2024)
d2023 = pd.read_csv(linkcrimen2023)
d2022 = pd.read_csv(linkcrimen2022)
d2021 = pd.read_csv(linkcrimen2021)
d2020 = pd.read_csv(linkcrimen2020)
d2019 = pd.read_csv(linkcrimen2019)
d2018 = pd.read_csv(linkcrimen2018)
d2017 = pd.read_csv(linkcrimen2017)

delitos = pd.concat([d2024,d2023,d2022,d2021,d2020,d2019,d2018,d2017])

ruidonoc = pd.read_csv(linkruidonoc)
ruidodia = pd.read_csv(linkruidodia)

obrasiniciadas = pd.read_csv(linkobrasiniciadas)

subte = pd.read_csv(linksubte)

gastronomia = pd.read_csv(linkgastronomia)

everdes = pd.read_csv(linkeverdes)

hospitales = pd.read_csv(linkhospitales)
