import os
import geopandas as gpd
import pandas as pd
from osgeo import gdal
from tqdm import tqdm
import geopandas as gpd
from run_command import run_command
import subprocess


#file and folder locations
dam_data = gpd.read_file('')
output_path = ''
luluc_data_folder = ''
lulc_data_format = 'ESACCI-LC-L4-LCCS-Map-300m-P1Y-{}-v2.0.7.tif'
temp_folder = ''


dam_floodInducing = dam_data[dam_data['Confirmatory_status'] == 'Likely Flood Inducing']
dam_protected = dam_data[dam_data['Confirmatory_status'] == 'Likely Flood Protecting']


def run_command(args, metsim=False, **kwargs):
    """Safely runs a command, logs and returns the returncode silently in case of no error. 
    Otherwise, raises an Exception
    """
    if isinstance(args, list):
        print("Running command:", " ".join(args))
    else:
        print("Running command:", args)
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)

    with p.stdout:
        for line in iter(p.stdout.readline, b''):  # b'\n'-separated lines
            print(line.decode("utf-8").strip())
        
    exitcode = p.wait()

    if exitcode == 0:
        print(f"Finished running command successfully: EXIT CODE {exitcode}")
    elif (exitcode == 0 and metsim):
        print(f"Finished running metsim successfully: EXIT CODE {exitcode}")
    else:
        print(f"ERROR Occurred with exit code: {exitcode}")
        raise Exception(f"Command failed with exit code: {exitcode}")
    
    return exitcode

# Classes
forest_class = [50, 60, 70, 80, 90]
cropland_class = [10, 11, 12]
urban_class = [190]

# Prepare the buffer and process each dam
for _, row in tqdm(dam_protected.iterrows(), total=dam_protected.shape[0]):
    dam_id = row['GRAND_ID']
    dam_name = row['DAM_NAME']
    print(f"Processing dam: {dam_name}")
    
    buffer = .001  # degrees
    geom = row['geometry'].buffer(buffer)  # Create buffer around dam geometry
    
    output_file = os.path.join(output_path, f"{dam_name}.csv")
    if os.path.exists(output_file):
        print(f"Skipping {dam_name} as output file already exists")
        continue
    lulc_df = pd.DataFrame(columns=['year', 'urban_cover', 'forest_cover', 'cropland_cover'])

    for date in range(1992, 2016):
        # Define paths
        lulc_data_path = f'{luluc_data_folder}/{lulc_data_format.format(date)}'
        temp_clipped_raster = f'{temp_folder}/{dam_name}_{date}_clipped.tif'
        if os.path.exists(temp_clipped_raster):
            print(f"Skipping {dam_name} for year {date}")
            continue
        # Save buffer geometry to a temporary shapefile
        buffer_shapefile = f'{temp_folder}/{dam_name}_buffer.shp'
        geom_gdf = gpd.GeoDataFrame({"geometry": [geom]}, crs=dam_floodInducing.crs)
        geom_gdf.to_file(buffer_shapefile)

        # Clip the raster using gdalwarp
        cmd = [
            "gdalwarp", 
            "-cutline", buffer_shapefile, 
            "-crop_to_cutline", 
            "-dstnodata", "0",  # Set nodata value
            lulc_data_path, 
            temp_clipped_raster
        ]
        run_command(cmd)

        # Analyze clipped raster to calculate land cover areas
        raster = gdal.Open(temp_clipped_raster)
        band = raster.GetRasterBand(1)
        lulc_array = band.ReadAsArray()
        pixel_area_km2 = (300 * 300) / 1e6  # 300m x 300m pixels, converted to sq.km

        urban_cover = (lulc_array == 190).sum() * pixel_area_km2
        forest_cover = sum((lulc_array == c).sum() for c in forest_class) * pixel_area_km2
        cropland_cover = sum((lulc_array == c).sum() for c in cropland_class) * pixel_area_km2

        # Append to DataFrame
        lulc_df = pd.concat([
            lulc_df, 
            pd.DataFrame([{
                'year': date,
                'urban_cover': urban_cover,
                'forest_cover': forest_cover,
                'cropland_cover': cropland_cover
            }])
        ], ignore_index=True)

    # Save to CSV
    lulc_df.to_csv(output_file, index=False)
    print(f"Saved LULC data for {dam_name} to {output_file}")
    