import streamlit as st
import pydeck
import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors

sensors = pd.read_csv("./data/sensors.csv")
readings = pd.read_csv("./data/readings.csv")

pollutant_selextbox = st.selectbox(
    "Which polluant would you like to visualize?",
    ("co", "no", "no2", "pm10", "o3", "pm1", "pm25", "relativehumidity", "temperature", "um003")
)

# Filtering for a pollutant type
filtered_sensors = sensors[sensors["pollutant_type"] == pollutant_selextbox]
filtered_sensors["first_reading"] = pd.to_datetime(filtered_sensors["first_reading"]).dt.strftime("%d-%m-%Y")
filtered_sensors["last_reading"]  = pd.to_datetime(filtered_sensors["last_reading"]).dt.strftime("%d-%m-%Y")

# Addig avg_reading column to the filtered_sensors table 
avg_readings = readings.groupby("sensor_id")["reading_value"].mean().round(2).reset_index()
avg_readings = avg_readings.rename(columns={"reading_value": "avg_reading"})
filtered_sensors = filtered_sensors.merge(avg_readings, on="sensor_id", how="left")

st.write(filtered_sensors)

# Selecting color for avg_reading
norm = mcolors.Normalize(
    vmin=filtered_sensors["avg_reading"].min(),
    vmax=filtered_sensors["avg_reading"].max()
)

cmap = cm.get_cmap("viridis")

filtered_sensors["color"] = filtered_sensors["avg_reading"].apply(
    lambda v: [int(c*255) for c in cmap(norm(v))[:3]]
)

# Visualizing the map
point_layer = pydeck.Layer(
    "ScatterplotLayer",
    map_style = "light",
    data=filtered_sensors,
    id="sensor-location",
    get_position=["longitude", "latitude"],
    get_color="color",
    pickable=True,
    auto_highlight=True,
    get_radius=4,
    radius_units="pixels"
)

view_state = pydeck.ViewState(
    latitude=56.16, longitude=10.21, controller=True, zoom = 9, pitch=0
)

chart = pydeck.Deck(
    point_layer,
    initial_view_state=view_state,
    tooltip={"text": "Avg {pollutant_type} reading: {avg_reading}\nFirst reading: {first_reading}\nLast reading: {last_reading}"},
)

event = st.pydeck_chart(chart, on_select="rerun", selection_mode="multi-object")

event.selection