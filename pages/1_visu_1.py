import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Visualisation 1", layout="wide")
st.title("Évolution comparative du loyer moyen et du revenu médian (1992-2024)")

RENT_FILES = {
    'loyer_montreal.csv': 'Montréal',
    'loyer_quebec.csv': 'Québec',
    'loyer_gatineau.csv': 'Gatineau',
    'loyer_ottawa.csv': 'Ottawa',
    'loyer_calgary.csv': 'Calgary',
    'loyer_edmonton.csv': 'Edmonton',
    'loyer_toronto.csv': 'Toronto',
    'loyer_vancouver.csv': 'Vancouver',
    'loyer_winnipeg.csv': 'Winnipeg'
}

HOUSING_MAP = {
    'Bachelor units': 'Studio',
    'One bedroom units': '1 chambre',
    'Two bedroom units': '2 chambres',
}

TARGET_REGIONS = 'Montréal|Québec|Gatineau|Ottawa|Calgary|Edmonton|Toronto|Vancouver|Winnipeg'

@st.cache_data
def load_data():
    '''
        Main orchestrator for data loading. Merges processed income and rent data.
        
        Args:
            None
        Returns:
            df_merged: The combined DataFrame with rent, income, effort rate, and status
    '''
    df_income = process_income_data('data/revenus.csv')
    df_rent = process_rent_data('data')
    df_merged = pd.merge(df_rent, df_income, on=['Year', 'City'])
    df_merged['Effort_Rate'] = (df_merged['Average_Rent'] / df_merged['Median_Income']) * 100
    df_merged = df_merged.dropna(subset=['Average_Rent', 'Median_Income'])
    df_merged['Status'] = df_merged['Effort_Rate'].apply(get_status)
    
    return df_merged


def get_status(rate):
    '''
        Evaluates the effort rate and returns a descriptive affordability status.

        Args:
            rate: The calculated effort rate float
        Returns:
            status: The affordability status string
    '''
    if rate < 30: return 'Abordable'
    elif rate < 45: return 'Élevé'
    else: return 'Extrême'


def process_income_data(path):
    """
        Loads and cleans the global income dataset from Statistics Canada.

        Args:
            path: The file path to the income CSV
        Returns:
            df_inc: The cleaned pandas DataFrame with Year, City, and Median_Income
    """
    df_inc_raw = pd.read_csv(path, encoding='utf-8', low_memory=False)
    df_inc = df_inc_raw[(df_inc_raw['Income source'] == 'Total income') & (df_inc_raw['Statistics'] == 'Median income (excluding zeros)') &
        (df_inc_raw['Age group'] == '15 years and over') & (df_inc_raw['Gender'] == 'Total - Gender')
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
    """
        Loops through individual city rent CSV files, cleans them, and combines them.

        Args:
            folder_path: The directory path containing the rent CSV files
        Returns:
            df_rents: The concatenated pandas DataFrame for all cities
    """
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
    """
        Sets the template for the hover bubble tooltips.

        Args:
            None
        Returns:
            template: The HTML formatted string for the tooltip
    """
    return (
        "<b>Année : %{x}</b><br>"
        "Loyer moyen : %{y}$<br>"
        "Revenu médian : %{customdata[0]:.0f}$<br>"
        "Taux d'effort : %{customdata[1]:.0f} %<br>"
        "Statut : <b>%{customdata[2]}</b><extra></extra>"
    )
    
def display_filters(df):
    """
        Renders the interactive filters and returns the user's selections.

        Args:
            df: The main pandas DataFrame containing the data
        Returns:
            selected_city: The city string chosen by the user
            selected_housing: The housing type string chosen by the user
    """
    col1, col2 = st.columns([1, 2])
    with col1:
        available_cities = df['City'].unique()
        selected_city = st.selectbox("Ville :", available_cities)

    with col2:
        available_housing = df['Housing_Type'].unique()
        selected_housing = st.radio(
            "Logement :", 
            available_housing, 
            index=1,
            horizontal=True
        )
        
    return selected_city, selected_housing


def filter_and_sort_data(df, city, housing_type):
    """
        Filters the dataset by city and housing type, then sorts chronologically.

        Args:
            df: The merged pandas DataFrame
            city: The selected city string
            housing_type: The selected housing type string
        Returns:
            filtered_df: The filtered and sorted pandas DataFrame
    """
    filtered_df = df[(df['City'] == city) & (df['Housing_Type'] == housing_type)]
    filtered_df = filtered_df.sort_values(by='Year', ascending=True)
    
    return filtered_df


def create_figure(filtered_df):
    """
        Generates the Plotly figure based on the filtered DataFrame.

        Args:
            filtered_df: The filtered pandas DataFrame to plot
        Returns:
            fig: The generated Plotly Graph Object figure
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=filtered_df['Year'],
        y=filtered_df['Median_Income'],
        mode='lines',
        name='Revenu médian',
        line=dict(color='#1f77b4', width=3),
        hoverinfo='skip'
    ))

    fig.add_trace(go.Scatter(
        x=filtered_df['Year'],
        y=filtered_df['Average_Rent'],
        mode='lines+markers',
        name='Loyer moyen',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8),
        hovertemplate=get_bubble_hover_template(),
        customdata=filtered_df[['Median_Income', 'Effort_Rate', 'Status']] 
    ))

    fig.update_layout(
        height=850,
        xaxis_title="Année",
        yaxis_title="Montant ($ CAD)",
        template="simple_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=30, l=50, r=50, b=200),
        hoverlabel=dict(
            font_size=16,    
            font_family="Arial",
        )
    )
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    return fig


selected_city, selected_housing = display_filters(my_df)
filtered_df = filter_and_sort_data(my_df, selected_city, selected_housing)
fig = create_figure(filtered_df)
st.plotly_chart(fig, use_container_width=True)