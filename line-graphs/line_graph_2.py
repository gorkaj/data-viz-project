# line graph showing seasonality in AQ and weather - aggregated by day/week/month
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


READINGS_PATH = "../data/readings.csv"
SENSORS_PATH = "../data/sensors.csv"

# Loading data
sensors_df = pd.read_csv(SENSORS_PATH)
readings = pd.read_csv(READINGS_PATH, parse_dates=["reading_datetime"])

readings_nonnull = readings.dropna(subset=["reading_value"]).copy()
sensors = sensors_df.merge(
    readings_nonnull[["sensor_id"]].drop_duplicates(),
    on="sensor_id",
    how="inner"
)

pollutants = sensors["pollutant_type"].unique().tolist()

for p in ["relativehumidity", "temperature", "um003"]:
    if p in pollutants:
        pollutants.remove(p)

# Filters
# Pollutant
selected_pollutant = st.sidebar.selectbox("Pollutant", sorted(pollutants))

if not selected_pollutant:
    st.sidebar.warning("No pollutants at this location")
    st.stop()

# Country
countries = (sensors.loc[sensors["pollutant_type"] == selected_pollutant, "country"].unique().tolist())
if not countries:
    st.warning("No countries found for that pollutant.")
    st.stop()
selected_country = st.sidebar.selectbox("Country", sorted(countries))

# Sensor
sensor_ids = sensors.loc[
    (sensors["pollutant_type"] == selected_pollutant) &
    (sensors["country"] == selected_country),
    "sensor_id"
].unique().tolist()

if not sensor_ids:
    st.warning("No sensors for that pollutant in this country.")
    st.stop()
sensor_id = st.sidebar.selectbox("Sensor ID", sorted(sensor_ids))

# Weather parameter
weather = st.sidebar.selectbox("Weather", ["wind_speed","rain"])

# Filter data by sensor_id
data = readings[readings["sensor_id"] == sensor_id].copy().sort_values("reading_datetime")

if data.empty:
    st.warning("No data found for that sensor.")
    st.stop()


# Aggregation options
agg_level = st.sidebar.selectbox("Aggregate by", ["Day", "Week", "Month"])

data["year"] = data["reading_datetime"].dt.year
years = sorted(data["year"].unique().tolist())
selected_years = st.sidebar.multiselect("Years", years, default=years)

data = data[data["year"].isin(selected_years)].copy()
if data.empty:
    st.warning("No data for selected years")
    st.stop()

if agg_level == "Day":
    data["time_unit"] = data["reading_datetime"].dt.dayofyear
    x_title = "Day"
elif agg_level == "Week":
    data["time_unit"] = data["reading_datetime"].dt.isocalendar().week.astype(int)
    x_title = "Week"
else:
    data["time_unit"] = data["reading_datetime"].dt.month
    x_title = "Month"

grouped = (
    data.groupby(["year", "time_unit"], as_index=False)[["reading_value", weather]].mean()
)

# pltting
st.subheader(f"{selected_pollutant} & {weather.title()} — Sensor {sensor_id}")
graph = go.Figure()

for year in sorted(grouped["year"].unique()):
    df_year = grouped[grouped["year"] == year]
    # pollution
    graph.add_trace(go.Scatter(
        x=df_year["time_unit"],
        y=df_year["reading_value"],
        name=f"{year} - pollution",
        line=dict(color="blue"),
        yaxis="y1"
    ))
    # weather
    graph.add_trace(go.Scatter(
        x=df_year["time_unit"],
        y=df_year[weather],
        name=f"{year} - {weather.replace('_',' ').title()}",
        line=dict(color="red"),
        yaxis="y2"
    ))

graph.update_layout(
    xaxis=dict(title=x_title),
    yaxis=dict(title="Pollution Level - avg"),
    yaxis2=dict(
        title=weather.replace("_", " ").title(),
        overlaying="y",
        side="right"
    ),
    legend=dict(orientation="h", y=1.05),
    height=500
)

st.plotly_chart(graph, use_container_width=True)
