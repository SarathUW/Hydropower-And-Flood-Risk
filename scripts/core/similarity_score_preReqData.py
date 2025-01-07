# Separate sections of this script contains code to generate pre-requisite data for the similarity score genration

import xarray as xr
import rioxarray as rxr
import geopandas as gpd
import os
import warnings
import pandas as pd

warnings.filterwarnings("ignore")


# User data
# We use the following datasets for creating the similarity scpre
#1. Precipitation - WorldClim precip dataset 2.5 minutes https://worldclim.org/data/worldclim21.html#google_vignette
precip_fp = '/precip_annual_mean.tif'
#2. Slope - Slope is derived from the SRTM DEM 10km dataset
slope_fp = '/srtm_slope.tif'
#3. urban land cover consensus dataset
urban_fp = '/consensus_full_class_9.tif'

study_sites_fp = '' #downstream river segments data
study_sites_vector_fp = '' #study sites data with dam names
control_sites_fp = '' #control sites data 


## Generating mean precipitation, slope and urban land cover for study sites
data = []

counter = 1
for index, dam in studySites_vector.iterrows():
    print(f'Dam number: {counter}. {dam["DAM_NAME"]}')
    dam_name = dam["DAM_NAME"]    
    studySite_filePath = f'{study_sites_fp}/{dam_name}_riverNet.geojson'
    
    if not os.path.exists(studySite_filePath):
        print(f'File not found: {studySite_filePath}')
        continue
    
    studySite_riverNet = gpd.read_file(studySite_filePath)
    # Buffer studysite by 0.01 degrees
    studySite_riverNet['geometry'] = studySite_riverNet.buffer(0.02)
    # Merge all polygons into one
    studySite_riverNet = studySite_riverNet.dissolve()
    # Get bounds of the study site
    studySite_bounds = studySite_riverNet.bounds
    minx, miny, maxx, maxy = studySite_bounds.iloc[0]

    # Clip the datasets and compute mean slope, porosity, and precipitation
    porosity_clipped = porosity.sel(lon=slice(minx, maxx), lat=slice(miny, maxy))
    # mean_porosity_site = float(porosity_clipped.GLDAS_porosity.mean(dim=['lat', 'lon']).values)
    # #set_porosity to 0.4 if it is nan
    # if pd.isnull(mean_porosity_site):
    #     mean_porosity_site = 0.4
    
    slope_clipped = slope.rio.clip(studySite_riverNet.geometry)
    fill_value = -9999.0
    notFillMask = slope_clipped != fill_value
    slope_clipped_notFill = slope_clipped.where(notFillMask)
    mean_slope_site = float(slope_clipped_notFill.sel(band=1).mean().values)
    
    precip_clipped = precip.rio.clip(studySite_riverNet.geometry)
    notFillMask = precip_clipped != fill_value
    precip_clipped_notFill = precip_clipped.where(notFillMask)
    mean_precip_site = float(precip_clipped_notFill.sel(band=1).mean().values)

     #clip the urrban dataset
    urban_clipped = urban.rio.clip(studySite_riverNet.geometry)
    fill_value = 255
    urban_threshold = 5 #%
    notFillMask = urban_clipped != fill_value
    urban_clipped_notFill = urban_clipped.where(notFillMask)
    urban_thresh_filtered = urban_clipped_notFill.where(urban_clipped_notFill > 5)
    total_pixels = urban_clipped_notFill.where(urban_clipped_notFill > -1).count().values
    total_urban_pixels = urban_thresh_filtered.count().values
    percentage_urban = total_urban_pixels / total_pixels * 100

    # Collect the data
    data.append({
        'Dam Name': dam_name,
        'Mean Slope': mean_slope_site,
        # 'Mean Porosity': mean_porosity_site,
        'Mean Precipitation': mean_precip_site,
        'Percentage Urban': percentage_urban
    })
    
    counter += 1

# Create the DataFrame from the collected data
studySites_dataset = pd.DataFrame(data)
studySites_dataset.to_csv('', index=False)

## Generating same for all control sites
controlSite_range = range(1,96)
data = []
counter_cs = 1
for cs_no in controlSite_range:
    cs_name = str(cs_no)
    print(f'{counter_cs}. Control Site number: {cs_name}')
    cs_fp = f'{control_sites_fp}/{cs_no}.geojson'
    
    cs_roi = gpd.read_file(cs_fp)
    # Buffer studysite by 0.01 degrees
    cs_roi['geometry'] = cs_roi.buffer(0.02)
    # Merge all polygons into one
    cs_roi = cs_roi.dissolve()
    # Get bounds of the study site
    cs_bounds = cs_roi.bounds
    minx, miny, maxx, maxy = cs_bounds.iloc[0]

    # Clip the datasets and compute mean slope, porosity, and precipitation
    porosity_clipped = porosity.sel(lon=slice(minx, maxx), lat=slice(miny, maxy))
    # mean_porosity_site = float(porosity_clipped.GLDAS_porosity.mean(dim=['lat', 'lon']).values)
    # #set_porosity to 0.4 if it is nan
    # if pd.isnull(mean_porosity_site):
    #     mean_porosity_site = 0.4
    
    slope_clipped = slope.rio.clip(cs_roi.geometry)
    fill_value = -9999.0
    notFillMask = slope_clipped != fill_value
    slope_clipped_notFill = slope_clipped.where(notFillMask)
    mean_slope_site = float(slope_clipped_notFill.sel(band=1).mean().values)
    
    precip_clipped = precip.rio.clip(cs_roi.geometry)
    notFillMask = precip_clipped != fill_value
    precip_clipped_notFill = precip_clipped.where(notFillMask)
    mean_precip_site = float(precip_clipped_notFill.sel(band=1).mean().values)

    #clip the urrban dataset
    urban_clipped = urban.rio.clip(cs_roi.geometry)
    fill_value = 255
    urban_threshold = 5 #%
    notFillMask = urban_clipped != fill_value
    urban_clipped_notFill = urban_clipped.where(notFillMask)
    urban_thresh_filtered = urban_clipped_notFill.where(urban_clipped_notFill > 5)
    total_pixels = urban_clipped_notFill.where(urban_clipped_notFill > -1).count().values
    total_urban_pixels = urban_thresh_filtered.count().values
    percentage_urban = total_urban_pixels / total_pixels * 100

    # print all computed info
    print(f'ControlSite: {cs_name}')
    print(f'Mean Slope: {mean_slope_site}')
    # print(f'Mean Porosity: {mean_porosity_site}')
    print(f'Mean Precipitation: {mean_precip_site}')
    print(f'Percentage Urban: {percentage_urban}')
    # Collect the data
    data.append({
        'ControlSite': cs_name,
        'Mean Slope': mean_slope_site,
        # 'Mean Porosity': mean_porosity_site,
        'Mean Precipitation': mean_precip_site,
        'Percentage Urban': percentage_urban
    })
    
    counter_cs += 1
    

controlSites_dataset = pd.DataFrame(data)
controlSites_dataset.to_csv('', index=False)


## Generating distance data for control site - study site pairings
study_sites_dataset = pd.read_csv('')
control_sites_dataset = pd.read_csv('')

epsg_mercator = 3857
distances_df = pd.DataFrame(index=study_sites_dataset['Dam Name'], columns=control_sites_dataset.ControlSite)

for site_index, site in studySites_vector.iterrows():
    site_name = site['DAM_NAME']
    print(f'Computing distances for {site_name}')
    studySite_filePath = f'{study_sites_fp}/{site_name}_riverNet.geojson'  
    studySite_riverNet = gpd.read_file(studySite_filePath)
    studySite_riverNet['geometry'] = studySite_riverNet.buffer(0.02)
    # Merge all polygons into one
    studySite_riverNet = studySite_riverNet.dissolve()
    studySite_riverNet = studySite_riverNet.to_crs(epsg=epsg_mercator)

    for control_idx, control_site in control_sites_dataset.iterrows():
        cs_name = int(control_site[0])
        print(f'Control site number: {cs_name}')
        cs_fp = f'{control_sites_fp}/{cs_name}.geojson'
    
        cs_roi = gpd.read_file(cs_fp)
        # Buffer studysite by 0.01 degrees
        cs_roi['geometry'] = cs_roi.buffer(0.02)
        # Merge all polygons into one
        cs_roi = cs_roi.dissolve()
        cs_roi = cs_roi.to_crs(epsg=epsg_mercator)
        distance_cs_study = studySite_riverNet.geometry.distance(cs_roi.geometry)
        print(distance_cs_study.values[0]/1E3)
        distances_df.loc[site_name, cs_name] = distance_cs_study.values[0]/1E3

distances_df.to_csv('', index=True)