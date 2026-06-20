import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import init_page, process_rent_data, TARGET_REGIONS, FONT, COLOR_INCOME, COLOR_RENT, plot_chart

st.set_page_config(page_title="Loyer vs Revenu", layout="wide")

init_page(
    title="Loyer moyen et revenu médian mensuel",
    subtitle="Évolution comparative dans les grandes villes canadiennes (1992–2024)"
)

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
        line=dict(color=COLOR_INCOME, width=3),
        hoverinfo='skip',
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df['Year'],
        y=filtered_df['Average_Rent'],
        mode='lines+markers',
        name='Loyer moyen',
        line=dict(color=COLOR_RENT, width=3),
        marker=dict(size=7, color=COLOR_RENT, line=dict(width=1.5, color='rgba(255,255,255,0.2)')),
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
plot_chart(fig)