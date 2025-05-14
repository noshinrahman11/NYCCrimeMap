from flask import Flask, render_template
import pandas as pd
import folium
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
import time
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/map')
def show_map():
    # Load dataset
    df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]  # Filter out invalid coordinates

    # Round coordinates to group nearby arrests
    df['rounded_lat'] = df['Latitude'].round(2)
    df['rounded_lon'] = df['Longitude'].round(2)

    # Count arrests at each rounded location
    arrest_counts = df.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
    arrest_counts = arrest_counts[arrest_counts['count'] >= 10]  # Filter low-activity points

    # Normalize counts for coloring
    min_count = arrest_counts['count'].min()
    max_count = arrest_counts['count'].max()
    arrest_counts['normalized_count'] = (arrest_counts['count'] - min_count) / (max_count - min_count)

    # Create map
    nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=10)
    colormap = folium.LinearColormap(['#fdaf9f', '#ff2d00'], vmin=0, vmax=1)

    # Add markers
    for _, row in arrest_counts.iterrows():
        radius = max(4, min(12, row['normalized_count'] * 20))  # Size scaled to intensity

        popup_text = (
            f"<b>Latitude:</b> {row['rounded_lat']}<br>"
            f"<b>Longitude:</b> {row['rounded_lon']}<br>"
            f"<b>Arrests:</b> {row['count']}"
        )
        folium.CircleMarker(
            location=[row['rounded_lat'], row['rounded_lon']],
            radius=radius,
            color=colormap(row['normalized_count']),
            fill=True,
            fill_color=colormap(row['normalized_count']),
            fill_opacity=0.6,
            popup=popup_text
        ).add_to(nyc_map)

    # Add static legend (HTML)
    legend_html = '''
     <div style="
         position: fixed;
         bottom: 50px;
         left: 50px;
         width: 150px;
         background-color: white;
         border: 2px solid grey;
         z-index:9999;
         font-size:14px;
         padding: 10px;
         line-height: 18px;
     ">
     <b>Arrest Intensity</b><br>
     <i style="background:#fdaf9f; width:18px; height:18px; display:inline-block;"></i> Low<br>
     <i style="background:#ff2d00; width:18px; height:18px; display:inline-block;"></i> High
     </div>
    '''
    nyc_map.get_root().html.add_child(folium.Element(legend_html))

    # Save map to HTML and render
    nyc_map.save("templates/map.html")
    return render_template("map.html")


@app.route('/data')
def data_summary():
    df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
    total_records = len(df)
    valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
    filtered = valid_coords.copy()
    filtered['rounded_lat'] = filtered['Latitude'].round(2)
    filtered['rounded_lon'] = filtered['Longitude'].round(2)

    # Count arrests by location
    arrest_counts = filtered.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
    filtered_points = len(arrest_counts[arrest_counts['count'] >= 10])
    max_arrests = arrest_counts['count'].max()

    # Get top 10 locations
    top_10 = arrest_counts.sort_values('count', ascending=False).head(10)

    # Load or initialize cache
    cache_file = 'geocache.json'
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            geocache = json.load(f)
    else:
        geocache = {}

    geolocator = Nominatim(user_agent="nyc-crime-map")
    top_coords = []

    for _, row in top_10.iterrows():
        lat = round(row['rounded_lat'], 2)
        lon = round(row['rounded_lon'], 2)
        key = f"{lat},{lon}"
        count = int(row['count'])

        if key in geocache:
            neighborhood = geocache[key]
        else:
            try:
                location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
                neighborhood = location.raw['address'].get('neighbourhood') or \
                               location.raw['address'].get('suburb') or \
                               location.raw['address'].get('city_district') or 'Unknown'
            except Exception:
                neighborhood = 'Unknown'
            geocache[key] = neighborhood
            time.sleep(1)  # Respect rate limits

        top_coords.append({
            'lat': lat,
            'lon': lon,
            'count': count,
            'neighborhood': neighborhood
        })

    # Save updated cache
    with open(cache_file, 'w') as f:
        json.dump(geocache, f, indent=2)

    return render_template("data.html",
        total_records=total_records,
        filtered_points=filtered_points,
        max_arrests=max_arrests,
        top_coords=top_coords
    )


if __name__ == '__main__':
    app.run(debug=True)

