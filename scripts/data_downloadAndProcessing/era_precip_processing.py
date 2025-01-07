# Using .onering conda env located at: /water3/saraths/Research_Files/Study2/marysville/.onering

# This script is used to convert ERA5 netcdf files to tif files. The ERA5 data is stored in netcdf format with daily precipitation data. 
# The script reads the netcdf file for each year, extracts the daily precipitation data, converts it to 0.1mm scale (same as IMERG data) 
# and exports it to a tif file. The tif file is stored in the folder specified by the user. The script also updates the crs of the exported tif file to EPSG:4326.

# Imports
import xarray as xr
import os
import numpy as np
import pandas as pd
import rasterio as rio
import rioxarray as rxr
from rasterio.transform import Affine


######## ERA5 nc to tif conversion ########
# User inputs
start_year = 1981
end_year = 2024
era_nc_folderPath = '/water3/saraths/Research_Files/Study2/ERA_precip/data_raw/'
era_tif_output_folderPath = '/water3/saraths/Research_Files/Study2/ERA_precip/processed/'
saveFile_suffix = 'IMERG' #ERA5 # - for purpose of running rat, we use the suffix 'IMERG' so that all files in the raw folder are annotated as IMERG files as RAT uses IMERG data as default.

# Generating a list of years, setting counters and lists for error handling.
years = np.arange(start_year,end_year)
counter = 0
error_files = []

## Processing and exporting era data from nc to tif file for each day in each year.
print('############## Processing and converting ERA5 data from nc to tif. Storing in the folder: ', era_tif_output_folderPath, ' ##############')
for year in years:
    print(f'Processing year: {year}')
    days = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31', freq='D')
    
    # reading era data
    era_data_fp = f'{era_nc_folderPath}ERA5_precip_{year}.nc'
    era_data = xr.open_dataset(era_data_fp)
    
    for day in days:
        try:
            print(day)
            output_fp = f'{era_tif_output_folderPath}{year}-{day.strftime("%m-%d")}_{saveFile_suffix}.tif'
            if os.path.exists(output_fp):
                print(f'File {output_fp} already exists. Skipping processing.')
                continue
            # Shifting days by 1 since we are time:00:00 data from ERA5 of the next day as the accumulated precipitation for the previous day.
            day_plus1 = day + pd.DateOffset(days=1)
            
            # Selecting the data for the day.
            try:
                era_data_slice = era_data.sel(time=day_plus1)
            except:
                era_data_slice = era_data.sel(time=day)

            # converting tp in era_data from m to 0.1mm (same scale as IMERG) and storing it in a new variable 'precipitation'
            era_data_slice['precipitation'] = era_data_slice['tp']*10000
            era_data_slice_filled = era_data_slice.fillna(0)

            # change the long from 0 to 360 to -180 to 180
            era_data_slice_filled = era_data_slice_filled.assign_coords(longitude=(((era_data_slice_filled.longitude + 180) % 360) - 180)).sortby('longitude')
            
            # Exporting data to tif file
            era_data_slice_filled['precipitation'].rio.to_raster(f'{output_fp}', crs='EPSG:4326', driver='GTiff', dtype='uint16')
            # Reading the exported tif file and updating the crs to EPSG:4326
            target_crs = rio.crs.CRS.from_epsg(4326) 
            with rio.open(output_fp, 'r+') as era_image_exported:
                era_image_exported.crs = target_crs
                era_image_exported.close()
            
            
        except Exception as e:
            print(f'Error in processing {year}_{day}. Detailed error: {e}')
            error_files.append(f'{year}_{day}')
            counter += 1
        else:
            print(f'Exported {year}_{day}')
        
    print(f'Processed year: {year}')

print(f'Processed {len(years)} years with {counter} errors in processing the files: {error_files}')
    
