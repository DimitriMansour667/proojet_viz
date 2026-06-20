import streamlit as st
import pandas as pd
import numpy as np

FONT = '"Inter", "Helvetica Neue", Arial, sans-serif'

COLOR_INCOME    = '#2dd4bf'  # revenu / positif
COLOR_RENT      = '#fb923c'  # loyer / charge
COLOR_MALE      = '#38bdf8'  # hommes
COLOR_FEMALE    = '#f472b6'  # femmes
COLOR_REMAINING = '#4ade80'  # reste à vivre
COLOR_THRESHOLD = '#f87171'  # seuil danger

CSS = """
<style>
  .page-title    { font-size:2rem; font-weight:700; color:#f9fafb;
                   text-align:center; margin-bottom:.2rem; }
  .page-subtitle { font-size:1rem; color:#9ca3af;
                   text-align:center; margin-bottom:1.5rem; }
</style>
"""

RENT_FILES = {
    'loyer_montreal.csv': 'Montréal', 'loyer_quebec.csv': 'Québec',
    'loyer_gatineau.csv': 'Gatineau', 'loyer_ottawa.csv': 'Ottawa',
    'loyer_calgary.csv': 'Calgary',   'loyer_edmonton.csv': 'Edmonton',
    'loyer_toronto.csv': 'Toronto',   'loyer_vancouver.csv': 'Vancouver',
    'loyer_winnipeg.csv': 'Winnipeg',
}

HOUSING_MAP = {
    'Bachelor units': 'Studio',
    'One bedroom units': '1 chambre',
    'Two bedroom units': '2 chambres',
    'Three bedroom units': '3 chambres',
}

HOUSING_ORDER = ['Studio', '1 chambre', '2 chambres', '3 chambres']

TARGET_REGIONS = 'Montréal|Québec|Gatineau|Ottawa|Calgary|Edmonton|Toronto|Vancouver|Winnipeg'

def init_page(title, subtitle):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f'<p class="page-title">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-subtitle">{subtitle}</p>', unsafe_allow_html=True)


def plot_chart(fig, **kwargs):
    _, col, _ = st.columns([1, 8, 1])
    with col:
        st.plotly_chart(fig, use_container_width=True, **kwargs)
    
    
def process_rent_data(folder_path):
    all_rents = []
    for file_name, city_name in RENT_FILES.items():
        try:
            df_city_raw = pd.read_csv(f"{folder_path}/{file_name}", encoding='utf-8', low_memory=False)
            if city_name == 'Gatineau':
                df_city = df_city_raw[df_city_raw['GEO'] == 'Ottawa-Gatineau, Quebec part, Ontario/Quebec'].copy()
            elif city_name == 'Ottawa':
                df_city = df_city_raw[df_city_raw['GEO'] == 'Ottawa-Gatineau, Ontario part, Ontario/Quebec'].copy()
            else:
                df_city = df_city_raw[df_city_raw['GEO'].str.contains(city_name, na=False, case=False)].copy()
            df_city = df_city[df_city['Type of structure'] == 'Row and apartment structures of three units and over']
            df_city['Housing_Type'] = df_city['Type of unit'].map(HOUSING_MAP)
            df_city = df_city.dropna(subset=['Housing_Type'])
            df_city = df_city[['REF_DATE', 'Housing_Type', 'VALUE']]
            df_city.columns = ['Year', 'Housing_Type', 'Average_Rent']
            df_city['City'] = city_name
            df_city['Year'] = df_city['Year'].astype(int)
            df_city['Average_Rent'] = pd.to_numeric(df_city['Average_Rent'], errors='coerce')
            all_rents.append(df_city)
        except FileNotFoundError:
            continue
    if not all_rents:
        return pd.DataFrame(columns=['Year', 'City', 'Housing_Type', 'Average_Rent'])
    return pd.concat(all_rents, ignore_index=True)
