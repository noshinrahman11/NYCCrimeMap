from flask import Flask, render_template
import pandas as pd
import folium

app = Flask(__name__)

@app.route('/')
def map():
    df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)] # remove rows with zero coordinates
    df['rounded_lat'] = df['Latitude'].round(3)
    df['rounded_lon'] = df['Longitude'].round(3)

    arrest_counts = df.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')

    # Create a Folium map centered on NYC
    nyc_map = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

    # # Add circles for each area
    # for _, row in arrest_counts.iterrows():
    #     folium.CircleMarker(
    #         location=[row['rounded_lat'], row['rounded_lon']],
    #         radius=row['count'] ** 0.5,  # scale radius
    #         popup=f"Arrests: {row['count']}",
    #         color='crimson',
    #         fill=True,
    #         fill_color='crimson',
    #         fill_opacity=0.6
    #     ).add_to(nyc_map)

    print("min:", arrest_counts.min())
    print("max:", arrest_counts.max())

    nyc_map.save("templates/map.html")
    return render_template("map.html")

if __name__ == '__main__':
    app.run(debug=True)
