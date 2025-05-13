from flask import Flask, render_template
import pandas as pd
import folium

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

        folium.CircleMarker(
            location=[row['rounded_lat'], row['rounded_lon']],
            radius=radius,
            color=colormap(row['normalized_count']),
            fill=True,
            fill_color=colormap(row['normalized_count']),
            fill_opacity=0.6,
            popup=f"Arrests: {row['count']}"
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

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/data')
def data_summary():
    df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
    total_records = len(df)
    valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
    filtered = valid_coords.copy()
    filtered['rounded_lat'] = filtered['Latitude'].round(2)
    filtered['rounded_lon'] = filtered['Longitude'].round(2)
    arrest_counts = filtered.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
    filtered_points = len(arrest_counts[arrest_counts['count'] >= 10])
    max_arrests = arrest_counts['count'].max()

    return render_template("data.html",
        total_records=total_records,
        filtered_points=filtered_points,
        max_arrests=max_arrests
    )


if __name__ == '__main__':
    app.run(debug=True)
