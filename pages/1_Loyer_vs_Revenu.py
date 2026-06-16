import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Loyer vs Revenu", layout="wide")

FONT = '"Inter", "Helvetica Neue", Arial, sans-serif'

CSS = """
<style>
  .page-title    { font-size:2rem; font-weight:700; color:#f9fafb;
                   text-align:center; margin-bottom:.2rem; }
  .page-subtitle { font-size:1rem; color:#9ca3af;
                   text-align:center; margin-bottom:1.5rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<p class="page-title">Loyer moyen et revenu médian mensuel</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="page-subtitle">Évolution comparative dans les grandes villes canadiennes (1992–2024)</p>',
    unsafe_allow_html=True,
)

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
TARGET_REGIONS = 'Montréal|Québec|Gatineau|Ottawa|Calgary|Edmonton|Toronto|Vancouver|Winnipeg'


@st.cache_data
def load_data():
    df_income = process_income_data('data/revenus.csv')
    df_rent   = process_rent_data('data')
    df_merged = pd.merge(df_rent, df_income, on=['Year', 'City'])
    df_merged['Effort_Rate'] = (df_merged['Average_Rent'] / df_merged['Median_Income']) * 100
    df_merged = df_merged.dropna(subset=['Average_Rent', 'Median_Income'])
    df_merged['Status'] = df_merged['Effort_Rate'].apply(get_status)
    return df_merged


def get_status(rate):
    if rate < 30: return 'Abordable'
    elif rate < 45: return 'Élevé'
    else: return 'Extrême'


def process_income_data(path):
    df_inc_raw = pd.read_csv(path, encoding='utf-8', low_memory=False)
    df_inc = df_inc_raw[
        (df_inc_raw['Income source'] == 'Total income') &
        (df_inc_raw['Statistics'] == 'Median income (excluding zeros)') &
        (df_inc_raw['Age group'] == '15 years and over') &
        (df_inc_raw['Gender'] == 'Total - Gender')
    ]
    df_inc = df_inc[df_inc['GEO'].str.contains(TARGET_REGIONS, na=False, case=False)]
    df_inc = df_inc[['REF_DATE', 'GEO', 'VALUE']]
    df_inc.columns = ['Year', 'City_Raw', 'Median_Income']
    df_inc['City'] = df_inc['City_Raw'].str.split(',').str[0].str.strip()
    df_inc.loc[df_inc['City_Raw'].str.contains('Ottawa', case=False, na=False), 'City'] = 'Ottawa'
    df_gatineau = df_inc[df_inc['City'] == 'Ottawa'].copy()
    df_gatineau['City'] = 'Gatineau'
    df_inc = pd.concat([df_inc, df_gatineau], ignore_index=True)
    df_inc['Year'] = df_inc['Year'].astype(int)
    df_inc['Median_Income'] = pd.to_numeric(df_inc['Median_Income'], errors='coerce') / 12
    return df_inc[['Year', 'City', 'Median_Income']]


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


my_df = load_data()


def get_bubble_hover_template():
    return (
        "<b>Année : %{x}</b><br>"
        "Loyer moyen : %{y}$<br>"
        "Revenu médian : %{customdata[0]:.0f}$<br>"
        "Taux d'effort : %{customdata[1]:.0f} %<br>"
        "Statut : <b>%{customdata[2]}</b><extra></extra>"
    )


def display_filters(df):
    col1, col2 = st.columns([1, 2])
    with col1:
        available_cities = df['City'].unique()
        selected_city = st.selectbox("Ville :", available_cities)
    with col2:
        available_housing = df['Housing_Type'].unique()
        selected_housing = st.radio("Logement :", available_housing, index=1, horizontal=True)
    return selected_city, selected_housing


def filter_and_sort_data(df, city, housing_type):
    filtered_df = df[(df['City'] == city) & (df['Housing_Type'] == housing_type)]
    return filtered_df.sort_values(by='Year', ascending=True)


def create_figure(filtered_df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=filtered_df['Year'],
        y=filtered_df['Median_Income'],
        mode='lines',
        name='Revenu médian',
        line=dict(color='#60a5fa', width=3),
        hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df['Year'],
        y=filtered_df['Average_Rent'],
        mode='lines+markers',
        name='Loyer moyen',
        line=dict(color='#fb7185', width=3),
        marker=dict(size=7, color='#fb7185', line=dict(width=1.5, color='rgba(255,255,255,0.2)')),
        hovertemplate=get_bubble_hover_template(),
        customdata=filtered_df[['Median_Income', 'Effort_Rate', 'Status']],
    ))

    fig.update_layout(
        height=520,
        template='plotly_dark',
        hovermode='x unified',
        font=dict(family=FONT, size=13, color='#d1d5db'),
        legend=dict(
            orientation='h',
            yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            bgcolor='rgba(17,24,39,0.7)',
            bordercolor='rgba(255,255,255,0.1)', borderwidth=1,
        ),
        xaxis=dict(
            title=dict(text='Année', font=dict(size=13, color='#9ca3af')),
            tickfont=dict(size=12, color='#9ca3af'),
            showgrid=False,
            linecolor='rgba(255,255,255,0.1)',
        ),
        yaxis=dict(
            title=dict(text='Montant mensuel ($ CAD)', font=dict(size=13, color='#9ca3af')),
            tickfont=dict(size=12, color='#9ca3af'),
            showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.07)',
            zeroline=False,
        ),
        margin=dict(t=20, l=60, r=30, b=60),
        hoverlabel=dict(
            bgcolor='#1f2937', font_size=13, font_family=FONT,
            bordercolor='rgba(255,255,255,0.15)',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig


selected_city, selected_housing = display_filters(my_df)
filtered_df = filter_and_sort_data(my_df, selected_city, selected_housing)
fig = create_figure(filtered_df)
st.plotly_chart(fig, use_container_width=True)
