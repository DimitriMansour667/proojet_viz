import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Écart H/F", page_icon="📊", layout="wide")

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
st.markdown(
    '<p class="page-title">Écart de pression locative — Hommes vs Femmes</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="page-subtitle">'
    'Part du revenu médian mensuel consacrée au loyer, par tranche d\'âge (1992–2024)'
    '</p>',
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
HOUSING_ORDER = ['Studio', '1 chambre', '2 chambres', '3 chambres']

INCOME_FILE = 'data/revenus_gender_age.csv'
YEAR_MIN, YEAR_MAX = 1992, 2024

AGE_MAP = {
    '15 to 24 years': '15–24 ans',
    '25 to 34 years': '25–34 ans',
    '35 to 44 years': '35–44 ans',
    '45 to 54 years': '45–54 ans',
    '55 to 64 years': '55–64 ans',
    '65 years and over': '65 ans +',
}

GENDER_COLORS = {'Homme': '#60a5fa', 'Femme': '#fb7185'}
CONNECTOR_COLOR = 'rgba(148,163,184,0.40)'
THRESHOLD = 30.0


@st.cache_data
def load_data():
    df_income = process_income_data()
    df_rent = process_rent_data('data')
    if df_income.empty or df_rent.empty:
        return pd.DataFrame()
    df = pd.merge(df_rent, df_income, on=['Year', 'City'])
    df['Effort_Rate'] = (df['Average_Rent'] / df['Median_Income']) * 100
    df = df.dropna(subset=['Average_Rent', 'Median_Income', 'Effort_Rate'])
    return df


def process_income_data():
    try:
        df = pd.read_csv(INCOME_FILE, encoding='utf-8')
    except FileNotFoundError:
        return pd.DataFrame()
    df = df[
        df['Age group'].isin(AGE_MAP) &
        df['Gender'].isin(GENDER_COLORS) &
        df['REF_DATE'].between(YEAR_MIN, YEAR_MAX) &
        df['VALUE'].notna()
    ].copy()
    df['Year'] = df['REF_DATE'].astype(int)
    df['Age'] = df['Age group'].map(AGE_MAP)
    df['Median_Income'] = pd.to_numeric(df['VALUE'], errors='coerce') / 12
    return df[['Year', 'City', 'Age', 'Gender', 'Median_Income']]


def process_rent_data(folder_path):
    all_rents = []
    for file_name, city_name in RENT_FILES.items():
        try:
            raw = pd.read_csv(f"{folder_path}/{file_name}", encoding='utf-8', low_memory=False)
        except FileNotFoundError:
            continue
        if city_name == 'Gatineau':
            city = raw[raw['GEO'] == 'Ottawa-Gatineau, Quebec part, Ontario/Quebec'].copy()
        elif city_name == 'Ottawa':
            city = raw[raw['GEO'] == 'Ottawa-Gatineau, Ontario part, Ontario/Quebec'].copy()
        else:
            city = raw[raw['GEO'].str.contains(city_name, na=False, case=False)].copy()
        city = city[city['Type of structure'] == 'Row and apartment structures of three units and over']
        city['Housing_Type'] = city['Type of unit'].map(HOUSING_MAP)
        city = city.dropna(subset=['Housing_Type'])
        city = city[['REF_DATE', 'Housing_Type', 'VALUE']]
        city.columns = ['Year', 'Housing_Type', 'Average_Rent']
        city['City'] = city_name
        city['Year'] = city['Year'].astype(int)
        city['Average_Rent'] = pd.to_numeric(city['Average_Rent'], errors='coerce')
        all_rents.append(city)
    if not all_rents:
        return pd.DataFrame(columns=['Year', 'City', 'Housing_Type', 'Average_Rent'])
    return pd.concat(all_rents, ignore_index=True)


my_df = load_data()

if my_df.empty or my_df['Gender'].nunique() < 2:
    st.warning(
        "**Données Hommes/Femmes introuvables.** Cette visualisation lit "
        f"`{INCOME_FILE}` (colonnes : REF_DATE, City, Age group, Gender, VALUE), "
        "avec le revenu médian ventilé par genre, ville et tranche d'âge. "
        "Vérifie que ce fichier est bien présent dans `data/`."
    )
    st.stop()

col1, col2 = st.columns(2)
with col1:
    cities = sorted(my_df['City'].unique())
    default_city = cities.index('Montréal') if 'Montréal' in cities else 0
    selected_city = st.selectbox("Ville :", cities, index=default_city)
with col2:
    housings = [h for h in HOUSING_ORDER if h in my_df['Housing_Type'].unique()]
    default_h = housings.index('1 chambre') if '1 chambre' in housings else 0
    selected_housing = st.selectbox("Type de logement :", housings, index=default_h)

chart_ph = st.empty()

years = sorted(
    my_df[(my_df['City'] == selected_city) &
          (my_df['Housing_Type'] == selected_housing)]['Year'].unique()
)
if not years:
    chart_ph.info("Aucune donnée pour cette combinaison ville / logement.")
    st.stop()

selected_year = st.slider(
    "Année :", min_value=int(years[0]), max_value=int(years[-1]),
    value=int(years[-1]), step=1,
)


def build_figure(df, city, housing, year):
    sub = df[(df['City'] == city) &
             (df['Housing_Type'] == housing) &
             (df['Year'] == year)]

    homme = sub[sub['Gender'] == 'Homme'].set_index('Age')
    femme = sub[sub['Gender'] == 'Femme'].set_index('Age')
    ages = [a for a in homme.index if a in femme.index]
    ages = sorted(ages, key=lambda a: homme.loc[a, 'Effort_Rate'])

    fig = go.Figure()

    for age in ages:
        xh = homme.loc[age, 'Effort_Rate']
        xf = femme.loc[age, 'Effort_Rate']
        ecart = xf - xh
        sign = '+' if ecart >= 0 else ''
        fig.add_trace(go.Scatter(
            x=[xh, xf], y=[age, age],
            mode='lines',
            line=dict(color=CONNECTOR_COLOR, width=3),
            hovertemplate=f"Écart (Femme − Homme) : {sign}{ecart:.1f} pts<extra>{age}</extra>",
            showlegend=False,
        ))

    for gender, color in GENDER_COLORS.items():
        g = sub[sub['Gender'] == gender].set_index('Age').reindex(ages).reset_index()
        fig.add_trace(go.Scatter(
            x=g['Effort_Rate'], y=g['Age'],
            mode='markers',
            name=gender,
            marker=dict(color=color, size=14, line=dict(color='rgba(255,255,255,0.25)', width=1.5)),
            customdata=g[['Median_Income', 'Average_Rent']].values,
            hovertemplate=(
                "<b>%{y} — " + gender + "</b><br>"
                "Taux d'effort : %{x:.1f} %<br>"
                "Revenu médian : %{customdata[0]:,.0f} $/mois<br>"
                "Loyer moyen : %{customdata[1]:,.0f} $/mois"
                "<extra></extra>"
            ),
        ))

    x_max = max(sub['Effort_Rate'].max() * 1.12, 45.0)
    fig.add_vline(
        x=THRESHOLD, line_dash='dash', line_color='#f87171', opacity=0.55,
        annotation_text='Seuil 30 %', annotation_position='top',
        annotation_font=dict(color='#f87171', size=11),
    )

    fig.update_layout(
        height=480,
        template='plotly_dark',
        font=dict(family=FONT, size=13, color='#d1d5db'),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            bgcolor='rgba(17,24,39,0.7)', bordercolor='rgba(255,255,255,0.1)', borderwidth=1,
        ),
        xaxis=dict(
            title=dict(text="Taux d'effort (% du revenu médian mensuel)",
                       font=dict(size=13, color='#9ca3af')),
            ticksuffix=' %', range=[0, x_max],
            tickfont=dict(size=12, color='#9ca3af'),
            showgrid=True, gridcolor='rgba(255,255,255,0.07)', zeroline=False,
            linecolor='rgba(255,255,255,0.1)',
        ),
        yaxis=dict(
            title='', categoryorder='array', categoryarray=ages,
            tickfont=dict(size=13, color='#d1d5db'), showgrid=False,
        ),
        margin=dict(t=40, l=90, r=40, b=60),
        hoverlabel=dict(bgcolor='#1f2937', font_size=13, font_family=FONT,
                        bordercolor='rgba(255,255,255,0.15)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig


fig = build_figure(my_df, selected_city, selected_housing, selected_year)
chart_ph.plotly_chart(fig, use_container_width=True)

st.caption(
    "Taux d'effort = loyer moyen mensuel / revenu médian mensuel. "
    "Revenu : StatCan 11-10-0239 (revenu total médian par genre et âge). "
    "Loyer : SCHL 34-10-0133 (moyenne des structures locatives)."
)
