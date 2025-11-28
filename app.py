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

st.set_page_config(
    page_title="HDI Components Explorer",
    page_icon="🌍",
    layout="wide")

# ---------------------------
# Tabs layout
# ---------------------------
tab1, tab4, tab2, tab3 = st.tabs([
    "🌐 Map View",
    "🔍 Scatter Plot",
    "🕸️ Radar Plot",
    "📈 Temporal Trends"
])

# ---------------------------
# 1. MAP VIEW
# ---------------------------

# Compute global min/max per metric across ALL years so the scale doesn't change
year_range = range(1990, 2024)  # 1990–2023 inclusive

def global_min_max(prefix: str):
    cols = [f"{prefix}_{y}" for y in year_range if f"{prefix}_{y}" in df.columns]
    if not cols:
        return (0.0, 1.0)
    col_min = df[cols].min().min()
    col_max = df[cols].max().max()
    return float(col_min), float(col_max)

# HDI is an index (0–1)
hdi_min, hdi_max = 0.0, 1.0
le_min, le_max = global_min_max("le")
eys_min, eys_max = global_min_max("eys")
mys_min, mys_max = global_min_max("mys")
gnipc_min, gnipc_max = global_min_max("gnipc")

range_color_map = {
    "hdi":   [hdi_min,   hdi_max],
    "le":    [le_min,    le_max],
    "eys":   [eys_min,   eys_max],
    "mys":   [mys_min,   mys_max],
    "gnipc": [gnipc_min, gnipc_max],
}

with tab1:
    st.subheader("Global HDI Overview")
    col1, col2 = st.columns([1, 3])

    label_map = {
        "hdi": "HDI",
        "le": "Life Expectancy",
        "eys": "Expected Years of Schooling",
        "mys": "Mean Years of Schooling",
        "gnipc": "GNI per Capita",
    }

    with col1:
        year_map = st.slider("Select Year", 1990, 2023, 2023, key="map_slider")
        selection = st.selectbox(
            "Select Component",
            tuple(label_map.keys()),
            format_func=lambda x: label_map.get(x, x),
        )

    with col2:
        # Map selection to the actual column (HDI index + raw values)
        data_col_map = {
            "hdi":   f"hdi_{year_map}",
            "le":    f"le_{year_map}",
            "eys":   f"eys_{year_map}",
            "mys":   f"mys_{year_map}",
            "gnipc": f"gnipc_{year_map}",  # <- uses gnipc_{}
        }
        value_col = data_col_map[selection]

        df_map = df.dropna(subset=[value_col]).reset_index(drop=True)

        labels = {
            f"hdi_{year_map}": "HDI",
            f"le_{year_map}": "Life Expectancy (years)",
            f"eys_{year_map}": "Expected Years of Schooling",
            f"mys_{year_map}": "Mean Years of Schooling",
            f"gnipc_{year_map}": "GNI per Capita (USD)",
        }

        fig_map = px.choropleth(
            df_map,
            locations="iso3",
            color=value_col,
            hover_name="country",
            color_continuous_scale="Viridis",
            labels=labels,
            range_color=range_color_map[selection],  # fixed per metric across years
        )

        # --- Hover templates with raw values; HDI remains index ---

        if selection == "hdi":
            customdata = df_map[[f"hdi_{year_map}", "subregion"]]
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                "<i>%{customdata[1]}</i><br><br>"
                "HDI: %{customdata[0]:.3f}<extra></extra>"
            )

        elif selection == "le":
            customdata = df_map[[f"le_{year_map}", "subregion"]]
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                "<i>%{customdata[1]}</i><br><br>"
                "Life Expectancy: %{customdata[0]:.1f} years<extra></extra>"
            )

        elif selection == "eys":
            customdata = df_map[[f"eys_{year_map}", "subregion"]]
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                "<i>%{customdata[1]}</i><br><br>"
                "Expected Years of Schooling: %{customdata[0]:.1f}<extra></extra>"
            )

        elif selection == "mys":
            customdata = df_map[[f"mys_{year_map}", "subregion"]]
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                "<i>%{customdata[1]}</i><br><br>"
                "Mean Years of Schooling: %{customdata[0]:.1f}<extra></extra>"
            )

        elif selection == "gnipc":
            customdata = df_map[[f"gnipc_{year_map}", "subregion"]]
            hovertemplate = (
                "<b>%{hovertext}</b><br>"
                "<i>%{customdata[1]}</i><br><br>"
                "GNI per Capita: %{customdata[0]:,.0f} USD<extra></extra>"
            )

        fig_map.update_traces(hovertemplate=hovertemplate, customdata=customdata)
        fig_map.update_layout(height=550)
        st.plotly_chart(fig_map, use_container_width=True)



# ---------------------------
# 2. RADAR PLOT
# ---------------------------
with tab2:
    st.subheader("Component Comparison (Normalized Values)")
    col1, col2 = st.columns([1, 3])

    global_ranges = {
        "Life Expectancy": (le_min, le_max),
        "Expected Years of Schooling": (eys_min, eys_max),
        "Mean Years of Schooling": (mys_min, mys_max),
        "GNI per Capita": (gnipc_min, gnipc_max),
    }

    categories = list(global_ranges.keys())

    with col1:
        year_radar = st.slider("Select Year", 1990, 2023, 2023)
        countries_radar = st.multiselect(
            "Select Countries",
            sorted(df["country"].unique()),
            max_selections=5,
        )

        if countries_radar:
            hdi_values = []
            countries_radar_valid = []
            hdi_display_values = []

            for country in countries_radar:
                hdi_series = df.loc[df["country"] == country, f"hdi_{year_radar}"]
                hdi = hdi_series.values[0] if not hdi_series.empty else None

                if pd.notna(hdi):
                    countries_radar_valid.append(country)
                    hdi_values.append(hdi)
                    hdi_display_values.append(f"{hdi:.3f}")
                else:
                    hdi_display_values.append("Not available")

            st.markdown("### HDI Values")
            hdi_table = pd.DataFrame({
                "Country": countries_radar,
                f"HDI ({year_radar})": hdi_display_values
            })
            st.dataframe(hdi_table, hide_index=True, width="stretch")

            countries_radar = countries_radar_valid

    with col2:
        radar_fig = go.Figure()
        color_palette = ["#008c5c", "#002f64", "#9b54f3", "#f98517", "#561e01"]

        for i, country in enumerate(countries_radar):
            row = df[df["country"] == country].iloc[0]
            subregion = row.get("subregion", "Unknown")

            le = row.get(f"le_{year_radar}", None)
            eys = row.get(f"eys_{year_radar}", None)
            mys = row.get(f"mys_{year_radar}", None)
            gnipc = row.get(f"gnipc_{year_radar}", None)

            raw_values = {
                "Life Expectancy": le,
                "Expected Years of Schooling": eys,
                "Mean Years of Schooling": mys,
                "GNI per Capita": gnipc,
            }

            norm_values = []
            hover_texts = []

            for comp, raw in raw_values.items():
                gmin, gmax = global_ranges[comp]
                norm = (raw - gmin) / (gmax - gmin) if raw is not None else 0
                norm_values.append(norm)

                if comp == "GNI per Capita":
                    hover_texts.append(
                        f"<b>{country}</b><br><i>{subregion}</i><br><br>"
                        f"{comp}: {raw:,.0f} USD"
                    )
                else:
                    hover_texts.append(
                        f"<b>{country}</b><br><i>{subregion}</i><br><br>"
                        f"{comp}: {raw:.1f}"
                    )

            norm_values.append(norm_values[0])
            theta = categories + [categories[0]]
            hover_texts.append(hover_texts[0])

            radar_fig.add_trace(
                go.Scatterpolar(
                    r=norm_values,
                    theta=theta,
                    text=hover_texts,
                    hoverinfo="text",
                    fill=None,
                    name=country,
                    line_color=color_palette[i % len(color_palette)],
                    line_width=3,
                )
            )

        radar_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            width=700,
            height=700,
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
    luminance_steps = [45, 75]  # darker for 1st country, lighter for 2nd


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
            # default=["Norway"],
            key="line_countries",
            max_selections=2
        )

    with col2:
        years_range = list(range(1990, 2024))
        line_fig = go.Figure()

        for c_idx, country in enumerate(countries_line):
            row = df[df["country"] == country].iloc[0]
            subregion = row.get("subregion", "Unknown")

            for comp, label in zip(
                    ["life_expectancy_index", "education_index", "income_index"],
                    ["Life Expectancy Index", "Education Index", "Income Index"]
            ):
                vals = [
                    df.loc[df["country"] == country, f"{comp}_{y}"].values[0]
                    if f"{comp}_{y}" in df.columns else None
                    for y in years_range
                ]

                if comp == "life_expectancy_index":
                    actuals = [
                        df.loc[df["country"] == country, f"le_{y}"].values[0]
                        if f"le_{y}" in df.columns else None
                        for y in years_range
                    ]
                    hovertext = "Life Expectancy: %{customdata:.1f} years"
                elif comp == "education_index":
                    mys = [
                        df.loc[df["country"] == country, f"mys_{y}"].values[0]
                        if f"mys_{y}" in df.columns else None
                        for y in years_range
                    ]
                    eys = [
                        df.loc[df["country"] == country, f"eys_{y}"].values[0]
                        if f"eys_{y}" in df.columns else None
                        for y in years_range
                    ]
                    actuals = list(zip(mys, eys))
                    hovertext = (
                        "Mean Years of Schooling: %{customdata[0]:.1f}<br>"
                        "Expected Years of Schooling: %{customdata[1]:.1f}"
                    )
                else:
                    actuals = [
                        df.loc[df["country"] == country, f"gnipc_{y}"].values[0]
                        if f"gnipc_{y}" in df.columns else None
                        for y in years_range
                    ]
                    hovertext = "GNI per capita: %{customdata:.1f} USD"

                line_fig.add_trace(go.Scatter(
                    x=years_range,
                    y=vals,
                    mode="lines",
                    name=f"{country} - {label}",
                    legendgroup=label,  # legend grouped by component
                    line=dict(color=color_for(label, c_idx), width=2),
                    customdata=actuals,
                    text=[country] * len(years_range),
                    hovertemplate=(
                            "<b>%{text}</b><br><i>" + subregion + "</i><br><br>"
                            "Year: %{x}<br>" + hovertext + "<br>"
                            + label + ": %{y:.3f}<extra></extra>"
                    )
                ))

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
                    ),
                    text=[country] * len(years_range),
                    hovertemplate="<b>%{text}</b><br><i>" + subregion + "</i><br><br>"
                                  "Year: %{x}<br>HDI: %{y:.3f}<extra></extra>"
                ))

        line_fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Index (0–1)",
            yaxis_range=[0, 1.2],
            width=1000,
            height=500
        )
        st.plotly_chart(line_fig, config={"responsive": True}, use_container_width=True)


# ---------------------------
# 4. SCATTER PLOT
# ---------------------------
with tab4:
    st.subheader("Relationship Between HDI and Components")
    col1, col2 = st.columns([1, 3])

    with col1:
        year_scatter = st.slider(
            "Select Year", 1990, 2023, 2023, key="scatter_slider"
        )

        # X-axis: raw value
        value_axis = st.selectbox(
            "X-axis (Raw Value)",
            ["le", "mys", "eys", "gnipc"],
            format_func=lambda x: {
                "le": "Life Expectancy (years)",
                "mys": "Mean Years of Schooling",
                "eys": "Expected Years of Schooling",
                "gnipc": "GNI per Capita (USD)",
            }.get(x, x),
            key="scatter_value_x",
        )

        regions = st.multiselect(
            "Highlight Regions",
            sorted(df["subregion"].unique()),
            key="multiselect_scatter",
        )

    with col2:
        x_col = f"{value_axis}_{year_scatter}"
        hdi_col = f"hdi_{year_scatter}"

        df_scatter = df.dropna(subset=[hdi_col, x_col]).reset_index(drop=True)

        # Palette for regions
        base_colors = px.colors.qualitative.Set2
        region_palette = {}

        def get_region_color(region_name):
            """Assign a unique color per highlighted region"""
            if region_name not in region_palette:
                region_palette[region_name] = base_colors[len(region_palette) % len(base_colors)]
            return region_palette[region_name]

        hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "<i>%{customdata[5]}</i><br><br>"
            "HDI: %{customdata[0]:.3f}<br>"
            "Life Expectancy: %{customdata[1]:.1f} years<br>"
            "Mean Years of Schooling: %{customdata[2]:.1f} years<br>"
            "Expected Years of Schooling: %{customdata[3]:.1f} years<br>"
            "GNI per Capita: %{customdata[4]:,.0f} USD"
            "<extra></extra>"
        )

        fig_scatter = go.Figure()

        # ------------------------------------------------------------------
        # CASE A — No regions selected → uniform color + NO legend
        # ------------------------------------------------------------------
        if not regions:
            customdata = df_scatter[
                [
                    hdi_col,
                    f"le_{year_scatter}",
                    f"mys_{year_scatter}",
                    f"eys_{year_scatter}",
                    f"gnipc_{year_scatter}",
                    "subregion",
                ]
            ].values

            fig_scatter.add_trace(
                go.Scatter(
                    x=df_scatter[x_col],
                    y=df_scatter[hdi_col],
                    mode="markers",
                    name="",  # no legend entry
                    showlegend=False,
                    marker=dict(
                        size=8,
                        color="#4c78a8",    # uniform blue color
                        opacity=1.0,
                    ),
                    hovertext=df_scatter["country"],
                    customdata=customdata,
                    hovertemplate=hovertemplate,  # <-- hover for ALL countries
                )
            )

        # ------------------------------------------------------------------
        # CASE B — Some regions selected → one trace per region + grey others
        # ------------------------------------------------------------------
        else:
            # Add highlighted regions (hover ON)
            for region in regions:
                sub_df = df_scatter[df_scatter["subregion"] == region]
                if sub_df.empty:
                    continue

                color = get_region_color(region)
                customdata = sub_df[
                    [
                        hdi_col,
                        f"le_{year_scatter}",
                        f"mys_{year_scatter}",
                        f"eys_{year_scatter}",
                        f"gnipc_{year_scatter}",
                        "subregion",
                    ]
                ].values

                fig_scatter.add_trace(
                    go.Scatter(
                        x=sub_df[x_col],
                        y=sub_df[hdi_col],
                        mode="markers",
                        name=region,
                        marker=dict(size=9, color=color, opacity=1.0),
                        hovertext=sub_df["country"],
                        customdata=customdata,
                        hovertemplate=hovertemplate,  # <-- hover for SELECTED regions
                    )
                )

            # Add all other regions as grey (hover OFF)
            other_df = df_scatter[~df_scatter["subregion"].isin(regions)]
            if not other_df.empty:
                customdata_other = other_df[
                    [
                        hdi_col,
                        f"le_{year_scatter}",
                        f"mys_{year_scatter}",
                        f"eys_{year_scatter}",
                        f"gnipc_{year_scatter}",
                        "subregion",
                    ]
                ].values

                fig_scatter.add_trace(
                    go.Scatter(
                        x=other_df[x_col],
                        y=other_df[hdi_col],
                        mode="markers",
                        name="Other regions",
                        marker=dict(size=7, color="lightgrey", opacity=0.4),
                        hovertext=other_df["country"],
                        customdata=customdata_other,
                        hovertemplate=None,   # ignore the template
                        hoverinfo="skip",     # <-- disables hover for this trace
                    )
                )

        # ------------------------------------------------------------------
        # Layout
        # ------------------------------------------------------------------
        x_labels = {
            "le": "Life Expectancy (years)",
            "mys": "Mean Years of Schooling",
            "eys": "Expected Years of Schooling",
            "gnipc": "GNI per Capita (USD)",
        }

        fig_scatter.update_layout(
            width=800,
            height=500,
            xaxis_title=x_labels[value_axis],
            yaxis_title="HDI",
            yaxis=dict(range=[0, 1.0]),
            legend=dict(
                title="Regions",
                orientation="v",
            ),
        )

        fig_scatter.update_xaxes(type="log")

        # Hide legend entirely when no regions selected
        if not regions:
            fig_scatter.update_layout(showlegend=False)

        st.plotly_chart(fig_scatter, use_container_width=True)
