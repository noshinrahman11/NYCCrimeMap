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


# @app.route('/map2')
# def map():
#     # Load arrest data
#     arrests_df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
#     arrests_df = arrests_df[(arrests_df['Latitude'] != 0) & (arrests_df['Longitude'] != 0)]

#     # Round coordinates
#     arrests_df['rounded_lat'] = arrests_df['Latitude'].round(3)
#     arrests_df['rounded_lon'] = arrests_df['Longitude'].round(3)

#     # Load neighborhood dataset
#     neighborhoods_df = pd.read_csv("nyc_neighborhoods.csv")  # replace with your actual file name
#     neighborhoods_df['rounded_lat'] = neighborhoods_df['lat'].round(3)
#     neighborhoods_df['rounded_lon'] = neighborhoods_df['lng'].round(3)

#     # Merge to attach neighborhood names
#     merged_df = pd.merge(
#         arrests_df,
#         neighborhoods_df[['neighborhood', 'rounded_lat', 'rounded_lon']],
#         on=['rounded_lat', 'rounded_lon'],
#         how='left'
#     )

#     # Group by coordinates and neighborhood
#     arrest_counts = (
#         merged_df.groupby(['rounded_lat', 'rounded_lon', 'neighborhood'])
#         .size()
#         .reset_index(name='count')
#     )

#     # Normalize for coloring
#     min_count = arrest_counts['count'].min()
#     max_count = arrest_counts['count'].max()
#     arrest_counts['normalized_count'] = (arrest_counts['count'] - min_count) / (max_count - min_count)

#     # Create Folium map
#     nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

#     # Use shades of red
#     colormap = folium.LinearColormap(['#ffcccc', '#ff0000'], vmin=0, vmax=1)

#     # Add circles
#     for _, row in arrest_counts.iterrows():
#         popup_text = f"{row['neighborhood'] if pd.notna(row['neighborhood']) else 'Unknown'}<br>Arrests: {row['count']}"
#         folium.CircleMarker(
#             location=[row['rounded_lat'], row['rounded_lon']],
#             radius=row['normalized_count'] * 20,
#             popup=popup_text,
#             color=colormap(row['normalized_count']),
#             fill=True,
#             fill_color=colormap(row['normalized_count']),
#             fill_opacity=0.6
#         ).add_to(nyc_map)

#     # Save map
#     nyc_map.save("templates/map.html")
#     return render_template("map.html")




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
    
    # Top 10 coordinates with the most arrests using a list
    top_coords = []
    top_10 = arrest_counts.sort_values('count', ascending=False).head(10)

    for _, row in top_10.iterrows():
        coord_data = {
            'lat': row['rounded_lat'],
            'lon': row['rounded_lon'],
            'count': int(row['count'])  
        }
        top_coords.append(coord_data)

    return render_template("data.html",
        total_records=total_records,
        filtered_points=filtered_points,
        max_arrests=max_arrests,
        top_coords=top_coords
    )


if __name__ == '__main__':
    app.run(debug=True)
