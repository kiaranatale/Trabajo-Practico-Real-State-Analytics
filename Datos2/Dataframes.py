import numpy as np
import pandas as pd


datos_argenprop_alquileres = pd.read_csv('Datos2/datos_argenprop_alquiler.tsv', sep = '\t')
datos_argenprop_ventas = pd.read_csv('Datos2/datos_argenprop_ventas (1).tsv', sep = '\t' )
datos_remax_alquileres = pd.read_csv('Datos2/datos_remax_alquiler.csv')
datos_remax_ventas = pd.read_csv('Datos2/datos_remax_venta.csv')

print(datos_argenprop_alquileres.info())
print(datos_argenprop_ventas.info())
print(datos_remax_alquileres.info())
print(datos_remax_ventas.info())
