import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

BASE_URL = "https://insideairbnb.com/get-the-data/"


# 1. Obtener soup
def get_soup(url):
    html = requests.get(url).content
    return BeautifulSoup(html, "html.parser")


# 2. Buscar tabla de ciudad
def get_city_table(soup, city_name):
    section = soup.find("h3", string=lambda x: x and city_name.lower() in x.lower())
    return section.find_next("table")


# 3. Extraer links CSV
def extract_csv_links(table):
    links = []
    for a in table.find_all("a", href=True):
        href = a["href"]
        if ".csv" in href:
            links.append(href)
    return links


# 4. Descargar CSV
def download_csv(link):
    r = requests.get(link)

    if link.endswith(".gz"):
        return pd.read_csv(io.BytesIO(r.content), compression="gzip")
    else:
        return pd.read_csv(io.BytesIO(r.content))


# 5. Descargar todos
def download_all_datasets(links):
    dfs = {}
    for link in links:
        print(f"Leyendo {link}")
        df = download_csv(link)
        name = link.split("/")[-1].replace(".csv.gz","").replace(".csv","")
        dfs[name] = df
    return dfs


# 6. Merge inteligente
def merge_datasets(dfs):
    df_final = dfs["listings"]

    if "reviews" in dfs:
        df_final = df_final.merge(
            dfs["reviews"],
            left_on="id",
            right_on="listing_id",
            how="left"
        )

    if "neighbourhoods" in dfs:
        df_final = df_final.merge(
            dfs["neighbourhoods"],
            on="neighbourhood",
            how="left"
        )

    return df_final


# 7. Función principal
def load_inside_airbnb(city):
    soup = get_soup(BASE_URL)
    table = get_city_table(soup, city)
    links = extract_csv_links(table)

    print("Archivos encontrados:")
    for l in links:
        print(l)

    dfs = download_all_datasets(links)

    print("\nTamaños:")
    for k,v in dfs.items():
        print(k, v.shape)

    df_final = merge_datasets(dfs)

    print("\nDF FINAL:", df_final.shape)
    return df_final
