#This script processing CIIRS and DMPS Nightlight data for study site locations
# and computes yearly nightlight dataset

import geopandas as gpd
import os
import geopandas as gpd
import pandas as pd
from osgeo import gdal
from tqdm import tqdm
import subprocess

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

#user data
dam_data = gpd.read_file('')
output_path = ''
nightLight_data_folder = ''
nightLight_data_format_pre2014 = 'Harmonized_DN_NTL_{}_calDMSP.tif'
nightLight_data_format_post2014 = 'Harmonized_DN_NTL_{}_simVIIRS.tif'
temp_folder = ''


dam_floodInducing = dam_data[dam_data['Confirmatory_status'] == 'Likely Flood Inducing']
dam_protected = dam_data[dam_data['Confirmatory_status'] == 'Likely Flood Protecting']

os.makedirs(temp_folder, exist_ok=True)


lit_threshold = 5
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
    nightLight_df = pd.DataFrame(columns=['year', 'lit_area', 'sum_of_radiance'])

    for date in range(1992, 2021):
        # Define paths
        if date < 2014:
            nightLight_data_format = nightLight_data_format_pre2014
        else:
            nightLight_data_format = nightLight_data_format_post2014
        nightLight_data_path = f'{nightLight_data_folder}/{nightLight_data_format.format(date)}'
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
            nightLight_data_path, 
            temp_clipped_raster
        ]
        run_command(cmd)

        # Analyze clipped raster to calculate land cover areas
        raster = gdal.Open(temp_clipped_raster)
        band = raster.GetRasterBand(1)
        nightLight_array = band.ReadAsArray()
        #calculating lit_pixels and sum of radiance
        lit_pixels = (nightLight_array > lit_threshold).sum()
        sum_of_radiance = nightLight_array.sum()


        # Append to DataFrame
        nightLight_df = pd.concat([
            nightLight_df, 
            pd.DataFrame([{
                'year': date,
                'lit_area': lit_pixels,
                'sum_of_radiance': sum_of_radiance
            }])
        ], ignore_index=True)

    # Save to CSV
    nightLight_df.to_csv(output_file, index=False)
    print(f"Saved nightLight data for {dam_name} to {output_file}")