import unittest
import pandas as pd
from app import app
import json
import os

class TestApp(unittest.TestCase):
    def test_csv_and_columns_loaded(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        self.assertFalse(df.empty, "CSV file is empty")
        self.assertIn('Latitude', df.columns, "Latitude column missing")
        self.assertIn('Longitude', df.columns, "Longitude column missing")

    def test_valid_coordinate_filtering(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
        self.assertGreater(len(valid_coords), 0, "Filtered DataFrame should be greater than 0")
        self.assertLess(len(valid_coords), len(df), "Not filtered, zero coordinates are still present")

    def test_rounded_coordinates(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)].copy()
        valid_coords['rounded_lat'] = valid_coords['Latitude'].round(2)
        valid_coords['rounded_lon'] = valid_coords['Longitude'].round(2)
        self.assertIn('rounded_lat', valid_coords.columns, "rounded_lat column missing")
        self.assertIn('rounded_lon', valid_coords.columns, "rounded_lon column missing")

    def test_grouped_arrest_counts(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)].copy()
        valid_coords['rounded_lat'] = valid_coords['Latitude'].round(2)
        valid_coords['rounded_lon'] = valid_coords['Longitude'].round(2)
        arrest_counts = valid_coords.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
        self.assertIn('count', arrest_counts.columns, "count column missing after groupby")
        self.assertTrue((arrest_counts['count'] >= 1).all(), "Some group entries have count < 1")
        self.assertGreaterEqual(arrest_counts['count'].max(), 10, "No groups have more than 10 arrests")

    def test_normalized_values_in_range(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)].copy()
        valid_coords['rounded_lat'] = valid_coords['Latitude'].round(2)
        valid_coords['rounded_lon'] = valid_coords['Longitude'].round(2)
        arrest_counts = valid_coords.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
        grouped = arrest_counts[arrest_counts['count'] >= 10].copy()
        min_count = grouped['count'].min()
        max_count = grouped['count'].max()
        grouped['normalized'] = (grouped['count'] - min_count) / (max_count - min_count)
        self.assertTrue((grouped['normalized'] >= 0).all(), "Normalization failed, values < 0")
        self.assertTrue((grouped['normalized'] <= 1).all(), "Normalization failed, values > 1")

    def test_top_10_arrest_locations(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)].copy()
        valid_coords['rounded_lat'] = valid_coords['Latitude'].round(2)
        valid_coords['rounded_lon'] = valid_coords['Longitude'].round(2)
        arrest_counts = valid_coords.groupby(['rounded_lat', 'rounded_lon']).size().reset_index(name='count')
        top_10 = arrest_counts.sort_values('count', ascending=False).head(10)
        self.assertEqual(len(top_10), 10, "Top 10 list should has 10 locations")
        for _, row in top_10.iterrows():
            self.assertTrue(-90 <= row['rounded_lat'] <= 90, f"Latitude {row['rounded_lat']} not in ny")
            self.assertTrue(-180 <= row['rounded_lon'] <= 180, f"Longitude {row['rounded_lon']} not in ny")

    def test_zero_coordinates_filetered(self):
        df = pd.read_csv("NYPD_Arrest_Data__Year_to_Date_.csv")
        valid_coords = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
        zero_coords = df[(df['Latitude'] == 0) | (df['Longitude'] == 0)]
        self.assertEqual(len(zero_coords), len(df) - len(valid_coords),
                         "Not all zero-coordinates removed")

    def test_flask_routes(self):
        tester = app.test_client(self)
        self.assertEqual(tester.get('/map').status_code, 200, "Route /map did not work")
        self.assertEqual(tester.get('/data').status_code, 200, "Route /data did not work")
        self.assertEqual(tester.get('/').status_code, 200, "Route / did not work")

    def test_geocache_structure(self):
        cache_file = 'geocache.json'
        self.assertTrue(os.path.exists(cache_file), "geocache.json file does not exist")
        with open(cache_file, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"geocache.json is not valid JSON: {e}")
        self.assertIsInstance(data, dict, "geocache.json does not contain a json object")


if __name__ == '__main__':
    unittest.main()
