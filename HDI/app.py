import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
    st.subheader("Component Comparison")
    col1, col2 = st.columns([1, 3])

    with col1:
        year_radar = st.slider("Select Year", 1990, 2023, 2023, key="radar_slider")
        countries_radar = st.multiselect(
            "Select Countries",
            sorted(df["country"].unique()),
            key="radar_countries"
        )

        if countries_radar:
            hdi_values = []
            countries_radar_valid = []
            for country in countries_radar:
                hdi = df.loc[df["country"] == country, f"hdi_{year_radar}"].values[0]
                if pd.notna(hdi):
                    countries_radar_valid.append(country)
                    hdi_values.append(hdi)
            countries_radar = countries_radar_valid

            st.markdown("### HDI Values")
            hdi_table = pd.DataFrame({
                "Country": countries_radar,
                f"HDI ({year_radar})": [f"{h:.3f}" for h in hdi_values]
            })

            st.dataframe(hdi_table, hide_index=True, use_container_width=True)
        else:
            hdi_values = []

    with col2:
        categories = ["Life Expectancy Index", "Education Index", "Income Index"]
        radar_fig = go.Figure()

        if countries_radar:
            min_hdi, max_hdi = min(hdi_values), max(hdi_values)
            norm = [(h - min_hdi) / (max_hdi - min_hdi + 1e-9) for h in hdi_values]

            colorscale = px.colors.sequential.Viridis

            for i, country in enumerate(countries_radar):
                row = df[df["country"] == country].iloc[0]
                values = [
                    row[f"life_expectancy_index_{year_radar}"],
                    row[f"education_index_{year_radar}"],
                    row[f"income_index_{year_radar}"],
                ]

                values.append(values[0])
                theta = categories + [categories[0]]

                color_idx = int(norm[i] * (len(colorscale) - 1))
                color = colorscale[color_idx]

                radar_fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=theta,
                    fill=None,
                    name=country,
                    line_color=color,
                    line_width=3,
                    hovertemplate="%{r:.3f}",
                ))

        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1.2])),
            showlegend=True,
            width=800,
            height=800,
        )

        st.plotly_chart(radar_fig, use_container_width=True)

# ---------------------------
# 3. TEMPORAL TRENDS
# ---------------------------
with tab3:
    st.subheader("Temporal Trends of HDI Components (Indices)")
    col1, col2 = st.columns([1, 3])

    base_hues = {
        "Life Expectancy Index": 165,  # teal
        "Education Index": 25,  # orange
        "Income Index": 254,  # purple
    }
    sat = 70  # saturation
    luminance_steps = [45, 70]  # darker for 1st country, lighter for 2nd


    def color_for(component_label: str, country_idx: int) -> str:
        lum = luminance_steps[country_idx % len(luminance_steps)]
        if component_label == "HDI":
            # grey, no hue
            return f"hsl(0, 0%, {lum}%)"
        else:
            hue = base_hues[component_label]
            return f"hsl({hue}, {sat}%, {lum}%)"


    with col1:
        countries_line = st.multiselect(
            "Select Countries",
            sorted(df["country"].unique()),
            default=["Norway"],
            key="line_countries",
            max_selections=2
        )

    with col2:
        years_range = list(range(1990, 2024))
        line_fig = go.Figure()

        for c_idx, country in enumerate(countries_line):
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
                    x=years_range, y=vals, mode="lines",
                    name=f"{country} - {label}",
                    legendgroup=label,  # legend grouped by component
                    line=dict(color=color_for(label, c_idx), width=2)
                )
                )

            # HDI plotting
            hdi_cols = [f"hdi_{y}" for y in years_range]
            if any(col in df.columns for col in hdi_cols):
                hdi_vals = [
                    df.loc[df["country"] == country, f"hdi_{y}"].values[0]
                    if f"hdi_{y}" in df.columns else None
                    for y in years_range
                ]
                line_fig.add_trace(go.Scatter(
                    x=years_range,
                    y=hdi_vals,
                    mode="lines",
                    name=f"{country} - HDI",
                    legendgroup="HDI",
                    line=dict(
                        color=color_for("HDI", c_idx),
                        width=2,
                        dash="dash"
                    )
                ))

        line_fig.update_traces(
            hovertemplate="Year=%{x}<br>Index=%{y:.3f}<extra></extra>"
        )

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
                "iso3": False,  # hide iso3 from hover
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
