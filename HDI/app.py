import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------
# Load data
# ---------------------------
def load_data():
    return pd.read_csv("hdi_processed.csv")

df = load_data()

st.set_page_config(page_title="HDI Components Explorer", layout="wide")
st.title("🌍 Human Development Index (HDI) Components Explorer")

# ---------------------------
# Tabs layout
# ---------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 Map View",
    "🕸️ Radar Plot",
    "📈 Temporal Trends",
    "🔍 Scatter Plot"
])

# ---------------------------
# 1. MAP VIEW
# ---------------------------
with tab1:
    st.subheader("Global HDI Overview")
    col1, col2 = st.columns([1, 3])

    label_map = {
    "hdi": "HDI",
    "life_expectancy_index": "Life Expectancy Index",
    "education_index": "Education Index",
    "income_index": "Income Index"
}

    with col1:
        year_map = st.slider("Select Year", 1990, 2023, 2023, key="map_slider")
        selection = st.selectbox(
            "Select Component",
            tuple(label_map.keys()),
            format_func=lambda x: label_map.get(x, x)
        )

    with col2:
        hdi_col = f"{selection}_{year_map}"
        fig_map = px.choropleth(
            df,
            locations="iso3",
            color=hdi_col,
            hover_name="country",
            hover_data={
                f"hdi_{year_map}": ':.3f',
                f"life_expectancy_index_{year_map}": ':.3f',
                f"education_index_{year_map}": ':.3f',
                f"income_index_{year_map}": ':.3f',
                "iso3": False,
            },
            labels={
                f"hdi_{year_map}": "HDI",
                f"life_expectancy_index_{year_map}": "Life Expectancy Index",
                f"education_index_{year_map}": "Education Index",
                f"income_index_{year_map}": "Income Index",
            },
            color_continuous_scale="Viridis",
            range_color=[0, 1],
            title=f"{label_map[selection]} by Country ({year_map})"  # ✅ use label_map here
        )

        fig_map.update_layout(height=700)
        st.plotly_chart(fig_map, use_container_width=True)


# ---------------------------
# 2. RADAR PLOT
# ---------------------------
with tab2:
    st.subheader("Component Comparison (Radar Plot — normalized 0–1)")
    col1, col2 = st.columns([1, 3])

    with col1:
        year_radar = st.slider("Select Year", 1990, 2023, 2023, key="radar_slider")
        countries_radar = st.multiselect(
            "Select Countries",
            sorted(df["country"].unique()),
            default=["Norway"],
            key="radar_countries"
        )

    with col2:
        categories = ["Life Expectancy Index", "Education Index", "Income Index"]
        radar_fig = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

        for i, country in enumerate(countries_radar):
            row = df[df["country"] == country].iloc[0]
            values = [
                row[f"life_expectancy_index_{year_radar}"],
                row[f"education_index_{year_radar}"],
                row[f"income_index_{year_radar}"],
            ]
            values.append(values[0])  # close the polygon
            theta = categories + [categories[0]]

            radar_fig.add_trace(go.Scatterpolar(
                r=values,
                theta=theta,
                fill='toself',
                name=country,
                line_color=colors[i % len(colors)]
            ))

        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1.2])),
            showlegend=True,
            width=800,
            height=800
        )
        st.plotly_chart(radar_fig, use_container_width=True)

# ---------------------------
# 3. TEMPORAL TRENDS
# ---------------------------
with tab3:
    st.subheader("Temporal Trends of HDI Components (Indices)")
    col1, col2 = st.columns([1, 3])

    with col1:
        countries_line = st.multiselect(
            "Select Countries",
            sorted(df["country"].unique()),
            default=["Norway"],
            key="line_countries"
        )

    with col2:
        years_range = [y for y in range(1990, 2024)]
        line_fig = go.Figure()

        for country in countries_line:
            for comp, label in zip(
                    ["life_expectancy_index", "education_index", "income_index"],
                    ["Life Expectancy Index", "Education Index", "Income Index"]
            ):
                vals = [
                    df.loc[df["country"] == country, f"{comp}_{y}"].values[0]
                    if f"{comp}_{y}" in df.columns else None
                    for y in years_range
                ]
                line_fig.add_trace(go.Scatter(
                    x=years_range,
                    y=vals,
                    mode="lines",
                    name=f"{country} - {label}"
                ))

        line_fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Index (0–1)",
            yaxis_range=[0, 1.2],
            width=1000,
            height=600
        )
        st.plotly_chart(line_fig, use_container_width=True)

# ---------------------------
# 4. SCATTER PLOT
# ---------------------------
with tab4:
    st.subheader("Relationship Between HDI Components (Indices)")
    col1, col2 = st.columns([1, 3])

    with col1:
        year_scatter = st.slider("Select Year", 1990, 2023, 2023, key="scatter_slider")
        x_axis = st.selectbox(
            "X-axis",
            ["life_expectancy_index", "education_index", "income_index"],
            format_func=lambda x: {
                "life_expectancy_index": "Life Expectancy Index",
                "education_index": "Education Index",
                "income_index": "Income Index"
            }.get(x, x),
            key="scatter_x"
        )
        y_axis = st.selectbox(
            "Y-axis",
            ["life_expectancy_index", "education_index", "income_index"],
            index=1,
            format_func=lambda x: {
                "life_expectancy_index": "Life Expectancy Index",
                "education_index": "Education Index",
                "income_index": "Income Index"
            }.get(x, x),
            key="scatter_y"
        )

    with col2:
        fig_scatter = px.scatter(
            df,
            x=f"{x_axis}_{year_scatter}",
            y=f"{y_axis}_{year_scatter}",
            color=f"hdi_{year_scatter}",
            hover_name="country",
            hover_data={
                f"hdi_{year_scatter}": ':.3f',
                f"life_expectancy_index_{year_scatter}": ':.3f',
                f"education_index_{year_scatter}": ':.3f',
                f"income_index_{year_scatter}": ':.3f',
                "iso3": False,   # hide iso3 from hover
            },
            labels={  # <-- friendly labels go here
                f"hdi_{year_scatter}": "HDI",
                f"life_expectancy_index_{year_scatter}": "Life Expectancy Index",
                f"education_index_{year_scatter}": "Education Index",
                f"income_index_{year_scatter}": "Income Index",
            },
            color_continuous_scale="Viridis",
            range_color=[0, 1],
            title="HDI Component Relationships (Normalized 0–1)"
        )
        fig_scatter.update_layout(
            width=800,
            height=800,
            xaxis=dict(range=[0, 1.1]),
            yaxis=dict(range=[0, 1.1])
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
