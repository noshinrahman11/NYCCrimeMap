from flask import Flask, render_template
import pandas as pd
import folium

app = Flask(__name__)

@app.route('/')
def map():
    df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)] # remove rows with zero coordinates
    df['rounded_lat'] = df['Latitude'].round(2)
    df['rounded_lon'] = df['Longitude'].round(2)

    arrest_counts = df.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
    arrest_counts = arrest_counts[arrest_counts['count'] >= 10]

    # Create a Folium map centered on NYC
    nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

    # Min arrests = 1, max = 490
    # print("min:", arrest_counts.min()) 
    # print("max:", arrest_counts.max())

    #Normalize the count to a range of 0-1
    min_count = arrest_counts['count'].min()
    max_count = arrest_counts['count'].max()
    arrest_counts['normalized_count'] = (arrest_counts['count'] - min_count) / (max_count - min_count)

    # colormap = folium.LinearColormap(['green', 'red'], vmin=0, vmax=1)
    colormap = folium.LinearColormap(['#fdaf9f', '#ff2d00'], vmin=0, vmax=1)

    # Add circles for each area with color based on normalized count
    for _, row in arrest_counts.iterrows():
        folium.CircleMarker(
            location=[row['rounded_lat'], row['rounded_lon']],
            radius = 6,  # fixed size
            color = colormap(row['normalized_count']),
            # radius=row['normalized_count'] * 20,  # scale radius
            popup=f"Arrests: {row['count']}",
            fill=True,
            fill_color=colormap(row['normalized_count']),
            fill_opacity=0.6
        ).add_to(nyc_map)

    nyc_map.save("templates/map.html")
    return render_template("map.html")

if __name__ == '__main__':
    app.run(debug=True)
