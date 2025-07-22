import os
import json
import geopandas as gpd
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely.validation import make_valid
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

def transform_points(points, img_bbox, img_width, img_height):
    xmin, ymin, xmax, ymax = img_bbox.bounds
    x_scale = (xmax - xmin) / img_width
    y_scale = (ymax - ymin) / img_height

    return [
        (xmin + x * x_scale, ymax - y * y_scale)
        for x, y in points
    ]

def fix_g(df):
    df = df.copy()
    df["geometry"] = df["geometry"].apply(lambda g: make_valid(g) if not g.is_valid else g)
    return df

def dissolve_all(df):
    geom = unary_union(df.geometry)
    return gpd.GeoDataFrame(geometry=[geom], crs=df.crs)

def label_and_diff(processed):
    merged = []
    cumulative = None
    for idx in sorted(processed.keys(), reverse=True):
        base = processed[idx]
        lbl = base["Label"].iloc[0]
        geom = base.geometry.iloc[0]

        if cumulative is not None:
            geom = geom.difference(unary_union([g for g in cumulative.geometry]))

        if not geom.is_empty:
            gdf = gpd.GeoDataFrame({"Label": [lbl], "geometry": [geom]}, crs=base.crs)
            merged.append(fix_g(gdf))
            cumulative = pd.concat([cumulative, gdf]) if cumulative is not None else gdf

    return pd.concat(merged, ignore_index=True)

def subtract_tiles_and_add_not_inundated(merged, tiles, original_labels):
    tiles = fix_g(tiles)
    original_union = unary_union(original_labels.geometry)
    known_union = unary_union(merged.geometry)

    not_inundated_polys = []
    for tile_geom in tiles.geometry:
        if not tile_geom.intersects(original_union):
            continue

        leftover = tile_geom.difference(known_union)
        if not leftover.is_empty:
            not_inundated_polys.append(leftover)

    if not_inundated_polys:
        not_inundated_gdf = gpd.GeoDataFrame(
            {"Label": ["Not inundated"] * len(not_inundated_polys), "geometry": not_inundated_polys},
            crs=merged.crs
        )
        not_inundated_gdf = fix_g(not_inundated_gdf)
        merged = pd.concat([merged, not_inundated_gdf], ignore_index=True)

    return merged

def process_json_and_save_geometries(shapefile_path, folder_path):
    tiles_df_all = gpd.read_file(shapefile_path)

    json_tile_ids = {f.replace(".json", "") for f in os.listdir(folder_path) if f.endswith(".json")}
    tiles_df = tiles_df_all[tiles_df_all["TileID"].isin(json_tile_ids)]

    if tiles_df.empty:
        raise ValueError("No matching TileIDs found between shapefile and JSON files.")

    if "TileID" not in tiles_df.columns or tiles_df.geometry is None:
        raise ValueError("The shapefile must have a 'TileID' column and valid geometries.")

    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    transformed_shapes = []

    for json_file in json_files:
        tile_id = json_file.replace('.json', '')
        tile_row = tiles_df[tiles_df["TileID"] == tile_id]

        if tile_row.empty:
            print(f"Skipping {json_file}: No matching TileID in shapefile.")
            continue

        img_bbox = tile_row.geometry.iloc[0].bounds

        json_path = os.path.join(folder_path, json_file)
        with open(json_path, 'r') as f:
            data = json.load(f)

        img_width = data.get("imageWidth")
        img_height = data.get("imageHeight")

        if img_width is None or img_height is None:
            print(f"Skipping {json_file}: Missing image width/height metadata.")
            continue

        for shape in data.get('shapes', []):
            label = shape.get('label', 'No label')
            points = shape.get('points', [])

            transformed_points = transform_points(points, box(*img_bbox), img_width, img_height)

            if len(transformed_points) == 2:
                (x1, y1), (x2, y2) = transformed_points
                polygon = box(x1, y1, x2, y2)
            elif len(transformed_points) >= 3:
                polygon = Polygon(transformed_points)
            else:
                continue

            transformed_shapes.append({"geometry": polygon, "Label": label})

    return gpd.GeoDataFrame(transformed_shapes, crs=tiles_df.crs), tiles_df

def main():
    processed = {}
    for idx, lbl in label_map.items():
        df = labels[labels["Label"] == lbl]
        df = fix_g(df)
        dissolved = dissolve_all(df)
        dissolved["Label"] = lbl
        processed[idx] = dissolved

    # Step 3: Remove overlaps and retain label priority
    merged = label_and_diff(processed)

    # Step 4: Add "not inundated" label for leftover tile areas
    merged = merged.explode(index_parts=True).reset_index(drop=True)
    merged = merged[merged.geometry.type.isin(["Polygon", "MultiPolygon"])]
    merged = subtract_tiles_and_add_not_inundated(merged, used_tiles, labels)

    # Step 5: Export result
    merged.to_file(output_file)
    print(f"Saved merged labels with 'Not inundated' areas to: {output_file}")

if __name__ == "__main__":
    load_dotenv()
    image_dir = Path(os.environ["Tilelocation"])
    workdir = Path(os.environ["workdirectory"])

    #folder_path = image_dir / 'Kloosterbeemden' / '2020'
    #folder_path = image_dir / 'Kloosterbeemden' / '2021'
    #folder_path = image_dir / 'Kloosterbeemden' / '2023'
    folder_path = image_dir / 'Kloosterbeemden' / '2024'

    #folder_path = image_dir / 'Schulensmeer' / '2020'
    #folder_path = image_dir / 'Schulensmeer' / '2021'
    #folder_path = image_dir / 'Schulensmeer' / '2023'
    #folder_path = image_dir / 'Schulensmeer' / '2024'


    tiles_path = workdir / 'Tiles_ortho_KB_buffer_selected.shp'
    #tiles_path = workdir / 'Tiles_ortho_SM_buffer_selected.shp'

    #output_file = workdir / 'Labels_KB_2020.shp'
    #output_file = workdir / 'Labels_KB_2021.shp'
    #output_file = workdir / 'Labels_KB_2023.shp'
    output_file = workdir / 'Labels_KB_2024.shp'

    #output_file = workdir / 'Labels_SM_2020.shp'
    #output_file = workdir / 'Labels_SM_2021.shp'
    #output_file = workdir / 'Labels_SM_2023.shp'
    #output_file = workdir / 'Labels_SM_2024.shp'

    # Step 1: Transform JSON shapes to GeoDataFrame & get only matching tiles
    labels, used_tiles = process_json_and_save_geometries(tiles_path, folder_path)

    # Step 2: Define label priority
    label_map = { # Labelmap for "Kloosterbeemden"
        4: "Inundated",
        3: "Other",
        2: "Reeds",
        1: "Uncertain"
    }

    #label_map = { # Labelmap for "Schulensmeer"
    #    4: "Other",
    #    3: "Reeds",
    #    2: "Inundated",
    #    1: "Uncertain"
    #}


    main()
