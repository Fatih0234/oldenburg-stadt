import pandas as pd

# Load the dataset
df = pd.read_csv("stadtverbesserer_snapshot.csv")

# Filter out rows with null coordinates
df_coords = df[df['latitude'].notna() & df['longitude'].notna()]

print("Coordinate Statistics:")
print(f"Total reports with coordinates: {len(df_coords)}")
print(f"Latitude range: {df_coords['latitude'].min()} to {df_coords['latitude'].max()}")
print(f"Longitude range: {df_coords['longitude'].min()} to {df_coords['longitude'].max()}")
print("\nSample coordinates:")
print(df_coords[['latitude', 'longitude']].head(10))
