# python -m streamlit run scatter_plot.py

import streamlit as st
import pandas as pd
import plotly.express as px

readings = pd.read_csv("./data/readings.csv")
sensors = pd.read_csv("./data/sensors.csv")

pollutants = sensors["pollutant_type"].unique().tolist()
selected_pollutant = st.sidebar.selectbox(
    "Which polluant would you like to visualize?",
    pollutants
)

sensors_for_selected_pollutant = sensors[sensors["pollutant_type"] == selected_pollutant]["sensor_id"].tolist()
sensor_id = st.sidebar.selectbox(
    "Which sensor would you like to visualize?",
    sensors_for_selected_pollutant
)

weather_param = st.sidebar.selectbox(
    "Compare with:",
    ("wind_speed", "rain")
)

# Slider: see if correlation changes by time (probably need higher frequency than 4/day)
lag = st.sidebar.slider(
    "Time lag (h):",
    min_value=-24,
    max_value=24,
    step=6,
    value = 0
)

if lag == 0:
    st.sidebar.write("Comparing pollution with **current** weather.")
elif lag > 0:
    st.sidebar.write(f"Comparing pollution with weather {lag} hours **later**.")
else:
    st.sidebar.write(f"Comparing pollution with weather {-lag} hours **before**.")

# filter for selected sensor id, should come from the map
readings_by_sensor = readings[readings["sensor_id"] == sensor_id]

# Shifting weather param by lag_steps (data needs to stay in chronological order)
lag_steps = - lag // 6
readings_by_sensor[weather_param] = readings_by_sensor[weather_param].shift(lag_steps)
readings_by_sensor = readings_by_sensor.dropna(subset=[weather_param])

# filter minus
readings_by_sensor_filtered = readings_by_sensor[readings_by_sensor["reading_value"] >= 0]

# Two-tab layout for filtered and unfiltered values
tab1, tab2 = st.tabs(["Filtered", "Unfiltered"])
with tab1:
    st.write(f"Filtered values: {readings_by_sensor.shape[0] - readings_by_sensor_filtered.shape[0]}")
    corr = readings_by_sensor_filtered[[weather_param, "reading_value"]].corr()
    st.write(f"Correlation: {round(corr[weather_param]['reading_value'], 2)}")
    fig1 = px.scatter(
        readings_by_sensor_filtered,
        x = weather_param,
        y = "reading_value",
        trendline="lowess"
    )
    st.plotly_chart(
        fig1,
        use_container_width=True,
        key=f"plotly_scatter_filtered")

with tab2:
    fig2 = px.scatter(
    readings_by_sensor,
    x = weather_param,
    y = "reading_value",
    trendline="lowess"
    )
    st.plotly_chart(
        fig2,
        use_container_width=True,
        key=f"plotly_scatter")
    