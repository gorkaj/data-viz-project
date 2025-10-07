# line graph showing how AQ and weather change together moment by moment - no aggregation
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

# Rolling average to smooth raw data
smooth = st.sidebar.checkbox("Rolling average (7 points)", value=False)
if smooth:
    data["reading_value"] = data["reading_value"].rolling(7, min_periods=1).mean()
    data[weather] = data[weather].rolling(7, min_periods=1).mean()


# Normalization
normalize = st.sidebar.checkbox("Normalize", value=False)


# Scaling values to 0-1
def minmax(s: pd.Series) -> pd.Series:
    smin, smax = s.min(), s.max()
    rng = smax - smin
    if pd.isna(rng) or rng == 0:
        return pd.Series(0.5, index=s.index)
    return (s - smin) / rng


pollutant_series_raw = data["reading_value"]
weather_series_raw = data[weather]

if normalize:
    pollutant_series_plot = minmax(pollutant_series_raw)
    weather_series_plot = minmax(weather_series_raw)
else:
    pollutant_series_plot = pollutant_series_raw
    weather_series_plot = weather_series_raw


# Correlation coefficent
corr = data["reading_value"].corr(data[weather])
st.sidebar.markdown(f"Correlation:{corr:.2f}")

# Plot
title = f"{selected_pollutant} / {weather.replace('_',' ').title()} — Sensor {sensor_id}"
st.subheader(title)

graph = go.Figure()

# pollutant
graph.add_trace(go.Scatter(
    x=data["reading_datetime"],
    y=pollutant_series_plot,
    name=selected_pollutant,
    line=dict(color="blue", width=1),
))

# weather
if normalize:
    graph.add_trace(go.Scatter(
        x=data["reading_datetime"],
        y=weather_series_plot,
        name=weather.replace("_", " ").title(),
        line=dict(color="red", width=1),
    ))
    graph.update_layout(
        xaxis=dict(title="Time"),
        yaxis=dict(title="Normalized data"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=450,
    )
else:
    graph.add_trace(go.Scatter(
        x=data["reading_datetime"],
        y=weather_series_plot,
        name=weather.replace("_", " ").title(),
        yaxis="y2",
        line=dict(color="red", width=1),
    ))
    graph.update_layout(
        xaxis=dict(title="Time"),
        yaxis=dict(title="Pollution level"),
        yaxis2=dict(title=weather.replace("_", " ").title(), overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=450,
    )

st.plotly_chart(graph, use_container_width=True)
