import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
from geopy.distance import geodesic
from sklearn.cluster import DBSCAN
import numpy as np

# =========================
# CONFIG
# =========================
SCHOOL_LAT = 22.769140
SCHOOL_LON = 88.343714

st.set_page_config(layout="wide")
st.title("🏫 School Student Geo-Analytics Dashboard")


df = pd.read_csv("Students.csv")
df = df[df['PIN_Code'] > 0]

area_summary = (
    df.groupby(["Area", "Latitude", "Longitude"])
    .size()
    .reset_index(name="students")
)

total_students = area_summary["students"].sum()

# =========================
# DISTANCE FROM SCHOOL
# =========================
def calc_distance(row):
    return round(
        geodesic((SCHOOL_LAT, SCHOOL_LON), (row["Latitude"], row["Longitude"])).km,
        2
    )

area_summary["distance_km"] = area_summary.apply(calc_distance, axis=1)

# =========================
# PERCENTAGE + RANK
# =========================
area_summary["percent"] = (area_summary["students"] / total_students * 100).round(2)
area_summary = area_summary.sort_values("students", ascending=False)
area_summary["rank"] = range(1, len(area_summary) + 1)

# =========================
# FILTER UI
# =========================
st.sidebar.header("🎛 Filters")

exclude_small = st.sidebar.checkbox("Exclude areas with < 10 students", value=True)
only_top20 = st.sidebar.checkbox("Include only the Top 20 areas", value=False)

if exclude_small:
    filtered_df = area_summary[area_summary["students"] >= 10].copy()
else:
    filtered_df = area_summary.copy()

# Recalculate rank & %
total_filtered = filtered_df["students"].sum()
filtered_df["percent"] = (filtered_df["students"] / total_filtered * 100).round(2)
filtered_df = filtered_df.sort_values("students", ascending=False)
filtered_df["rank"] = range(1, len(filtered_df) + 1)

if only_top20:
    filtered_df = filtered_df[filtered_df['rank'] <= 20]

# =========================
# SMART CLUSTERING (DBSCAN)
# =========================
coords = filtered_df[["Latitude", "Longitude"]].values



# =========================
# MAP
# =========================
m = folium.Map(
    location=[SCHOOL_LAT, SCHOOL_LON],
    zoom_start=12,
    min_zoom=10,
    max_zoom=16,
)

# School marker
folium.CircleMarker(
    location=[SCHOOL_LAT, SCHOOL_LON],
    radius=8,
    color="red",
    fill=True,
    fill_opacity=1,
    tooltip="🏫 St Augustine's Day School"
).add_to(m)

# Scale radius from 1–10
max_students = filtered_df["students"].max() if len(filtered_df) else 1

for _, row in filtered_df.iterrows():

    radius = 1 + 9 * (row["students"] / max_students)

    tooltip_text = (
        f"📍 Area: {row['Area']}<br>"
        f"👨‍🎓 Students: {row['students']}<br>"
        f"📊 %: {row['percent']}%<br>"
        f"🏆 Rank: #{row['rank']}<br>"
        f"📏 Distance: {row['distance_km']} km"
    )

    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=radius,
        color="blue",
        fill=True,
        fill_opacity=0.6,
        tooltip=folium.Tooltip(tooltip_text, sticky=True)
    ).add_to(m)

# Restrict map to local area around school
m.fit_bounds([
    [SCHOOL_LAT - 0.05, SCHOOL_LON - 0.05],
    [SCHOOL_LAT + 0.05, SCHOOL_LON + 0.05]
])

# =========================
# DISPLAY MAP
# =========================
st.subheader("🗺 Student Distribution Map")
st_folium(m, width=1200, height=650)

# =========================
# ANALYTICS TABLE
# =========================
st.subheader("📊 Area-wise Student Summary")
st.dataframe(filtered_df)
