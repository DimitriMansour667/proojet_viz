import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Visu 3", page_icon="📊", layout="wide")

CITY_FILES = [
    "data/loyer_calgary.csv", "data/loyer_edmonton.csv", "data/loyer_montreal.csv",
    "data/loyer_ottawa.csv",  "data/loyer_gatineau.csv", "data/loyer_quebec.csv",
    "data/loyer_toronto.csv", "data/loyer_vancouver.csv", "data/loyer_winnipeg.csv",
]

AGE_GROUPS = {
    "25 to 34 years": "25–34 ans",
    "35 to 44 years": "35–44 ans",
    "45 to 54 years": "45–54 ans",
    "55 to 64 years": "55–64 ans",
}

UNIT_TYPES = {
    "Bachelor units":      "Studio",
    "One bedroom units":   "1 chambre",
    "Two bedroom units":   "2 chambres",
    "Three bedroom units": "3 chambres",
}

BASE_YEAR    = 1992
CURRENT_YEAR = 2024

N_COLS    = len(AGE_GROUPS)
GAP       = 0.05
PIE_WIDTH = (1.0 - (N_COLS - 1) * GAP) / N_COLS
PIE_Y     = [0.05, 0.88]


def pie_x(col_i):
    x0 = (col_i - 1) * (PIE_WIDTH + GAP)
    return [x0, x0 + PIE_WIDTH]


@st.cache_data
def load_data():
    income_raw = pd.read_csv("data/revenus_age.csv", low_memory=False)
    income = income_raw[
        (income_raw["GEO"] == "Canada") &
        (income_raw["Age group"].isin(AGE_GROUPS)) &
        (income_raw["Gender"] == "Total - Gender") &
        (income_raw["Income source"] == "Employment income") &
        (income_raw["Statistics"] == "Median income (excluding zeros)") &
        (income_raw["VALUE"].notna())
    ][["REF_DATE", "Age group", "VALUE"]].rename(columns={"REF_DATE": "year", "VALUE": "income"})

    rent_raw = pd.concat([pd.read_csv(f, low_memory=False) for f in CITY_FILES])
    rent_raw = rent_raw[
        (rent_raw["Type of structure"] == "Row and apartment structures of three units and over") &
        (rent_raw["VALUE"].notna())
    ]

    rent_by_unit = {}
    for unit in UNIT_TYPES:
        rent = (
            rent_raw[rent_raw["Type of unit"] == unit]
            .groupby("REF_DATE")["VALUE"].mean()
            .reset_index()
            .rename(columns={"REF_DATE": "year", "VALUE": "monthly_rent"})
        )
        rent["annual_rent"] = rent["monthly_rent"] * 12
        rent_by_unit[unit] = rent

    return income, rent_by_unit


def build_figure(income, rent_by_unit):
    fig = make_subplots(
        rows=1, cols=N_COLS,
        specs=[[{"type": "pie"}] * N_COLS],
        column_titles=list(AGE_GROUPS.values()),
        horizontal_spacing=GAP,
    )

    frames = []
    for unit, _ in UNIT_TYPES.items():
        merged = income.merge(rent_by_unit[unit], on="year")
        merged["burden"] = merged["annual_rent"] / (merged["income"] * 0.75) * 100

        traces = []
        for col_i, (age_key, _) in enumerate(AGE_GROUPS.items(), start=1):
            row     = merged[merged["Age group"] == age_key]
            base    = row[row["year"] == BASE_YEAR]["burden"].values
            current = row[row["year"] == CURRENT_YEAR]["burden"].values
            if not len(base) or not len(current):
                continue

            burden   = current[0]
            increase = max(current[0] - base[0], 0)

            traces.append(go.Pie(
                values=[burden, max(100 - burden, 0)],
                labels=["Loyer (total)", "Reste à vivre"],
                marker_colors=["#C25A00", "#2A7D4F"],
                marker_line={"color": "#ffffff", "width": 2},
                hole=0.55,
                direction="clockwise",
                sort=False,
                showlegend=(col_i == 1),
                textinfo="none",
                domain={"x": pie_x(col_i), "y": PIE_Y},
                title={
                    "text": f"<span style='color:#cc0000;font-size:15px'><b>+{increase:.1f}%</b></span><br><span style='font-size:10px;color:#999'>depuis {BASE_YEAR}</span>",
                    "position": "middle center",
                },
                hovertemplate="<b>%{label}</b><br>%{value:.1f} % du revenu<extra></extra>",
            ))

        frames.append(go.Frame(data=traces, name=unit))

    for trace in frames[2].data:
        fig.add_trace(trace)

    fig.frames = frames

    fig.update_layout(
        paper_bgcolor="#ffffff",
        font={"color": "#222", "family": "Inter, sans-serif"},
        height=460,
        margin={"l": 20, "r": 20, "t": 100, "b": 80},
        legend={"orientation": "h", "x": 0.5, "xanchor": "center", "y": -0.08, "bgcolor": "rgba(0,0,0,0)"},
        updatemenus=[{
            "type": "buttons",
            "direction": "right",
            "x": 0.5, "xanchor": "center",
            "y": 1.12, "yanchor": "bottom",
            "showactive": True,
            "active": 2,
            "bgcolor": "#f5f5f5",
            "bordercolor": "#ddd",
            "borderwidth": 1,
            "font": {"size": 13, "color": "#444"},
            "buttons": [
                {
                    "label": label,
                    "method": "animate",
                    "args": [[unit], {"frame": {"duration": 500, "redraw": True}, "transition": {"duration": 400}, "mode": "immediate"}],
                }
                for unit, label in UNIT_TYPES.items()
            ],
        }],
    )

    for ann in fig.layout.annotations:
        ann.update(font={"size": 13, "color": "#222"})

    return fig


st.title("Une hausse des loyers qui affecte particulièrement les jeunes actifs et les plus âgés")
st.markdown(f"Part du revenu médian d'emploi consacrée au loyer en {CURRENT_YEAR} vs {BASE_YEAR}, par tranche d'âge, moyenne des grandes RMR canadiennes")

income, rent_by_unit = load_data()
st.plotly_chart(build_figure(income, rent_by_unit), use_container_width=True)

st.caption("Revenu : revenu médian d'emploi (Canada, 2024 $, StatCan 11-10-0239). Loyer : moyenne des grandes RMR (CMHC 34-10-0133).")
st.caption("Revenu net estimé (brut × 0,75, taux effectif moyen ~25 %, fédéral + provincial)")
