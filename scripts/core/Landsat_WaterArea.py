##Imports
import geopandas as gpd
import warnings
from shapely.geometry import box, Polygon
from data_downloader import data_download
import pystac_client
import planetary_computer
import odc.stac
import matplotlib.pyplot as plt
import rasterio as rio
from pystac.extensions.eo import EOExtension as eo
from rasterio.mask import mask
import stackstac
from matplotlib.colors import Normalize
import numpy as np
import pyproj
import time
import pandas as pd
import altair as alt
import os
import xarray as xr
import rioxarray as rxr
import rasterio as rio

warnings.filterwarnings('ignore')

def water_area(water_mask, res):
    water_pixels = water_mask.sum()
    pixel_area = res**2
    wa = water_pixels * pixel_area
    return(wa)

#OTSU Thresholding function
def otsu(image_waterIndex, thresh_hard = 0.375):
    #Image has to be normalised before applying the automated OTSU threshold
    norm = Normalize(vmin = -1, vmax = 1)
    image_waterIndex_norm = norm(image_waterIndex)
    try:
        threshold = threshold_otsu(image_waterIndex_norm)
    except:
        threshold = thresh_hard  # set a hard-coded threshold value
        print(f'OTSU method failed, used {threshold} as threshold')
    return threshold 

crs = 3857 #EPSG:x
buffer = 100 #meters
buffer_deg = buffer/112000
time_of_interest= ""
key = '' #Microsoft Planetary Computer API key
satellite = 'landsat'
satellite_query_param = "landsat-c2-l2"
cloud_cover = 20

#Reading dam roi data
dams_ROI_fp = ''
dams_ROI = gpd.read_file(dams_ROI_fp)
num_dams = len(dams_ROI['DAM_NAME'])

counter_dams = 1
error_dams = []

#Starting run timer
start_time = time.perf_counter()
for dam_name in dams_ROI['DAM_NAME'][counter_dams - 1:]:
    
    print(f'{counter_dams}/{num_dams}. {dam_name}')
    output_fp = f'/{dam_name}.csv' #Change this output location
    if not os.path.exists(output_fp):
        try:
            dam_gdf = dams_ROI[dams_ROI['DAM_NAME'] == dam_name]
            #Buffering geometry
            res_roi_buffer_gdf = dam_gdf.copy()
            res_roi_buffer_gdf_deg = dam_gdf.copy()
            #set crs for correct buffering
            res_roi_buffer_gdf = res_roi_buffer_gdf.to_crs(crs)
            #Buffering and extracting buffered geometry
            res_roi_buffer_gdf['geometry'] = res_roi_buffer_gdf.geometry.buffer(buffer)
            res_roi_buffer_gdf_deg['geometry'] = res_roi_buffer_gdf_deg.geometry.buffer(buffer_deg)

            res_geom = res_roi_buffer_gdf.geometry.values[0]

            ##Downloading data from Microsoft Planetary Computer
            res_bbox = box(*dam_gdf.total_bounds)

            # bbox_of_interest = [-122.2751, 47.5469, -121.9613, 47.7458]
            # time_of_interest2 = "2021-01-01/2021-12-31"

            bbox2 = list(dam_gdf.total_bounds)
            bbox_deg = list(res_roi_buffer_gdf_deg.total_bounds)
            # connecting to mcpc and checking for available imagery
            l8_items = data_download(time_of_interest, satellite, satellite_query_param, key, area_of_interest= res_bbox, cloud_cover=cloud_cover, enclose_roi = True)
            
            
            res_area_l8 = []
            cloud_cover_series_l8 = []
            counter = 1
            for item in l8_items:
                pekel_dam_clipped_fp = f'/{dam_name}.tif' #use pekel data clipped to geometry here
                clipped = rxr.open_rasterio(pekel_dam_clipped_fp)
                pekel_shape = clipped.shape[-2:1]
                dam_geom_mask = rio.features.geometry_mask([res_geom], out_shape=clipped.shape[-2:], transform=clipped.rio.transform(), invert=True)
                dam_pekel_buffer = clipped.where(dam_geom_mask)
                try:
                    ds = stackstac.stack(item, bounds_latlon=bbox_deg, epsg=crs, resolution = 30)
                    l8_green = ds.sel(band="green")[0].compute()
                    l8_swir = ds.sel(band="swir16")[0].compute()
                    l8_nir = ds.sel(band="nir08")[0].compute()
                    l8_qa = ds.sel(band="qa_pixel")[0].compute()
                    res_geom_mask = rio.features.geometry_mask([res_geom], out_shape=l8_green.shape[-2:], transform=l8_green.transform, invert=True)
                    l8_green_roi = l8_green.where(res_geom_mask)
                    l8_swir_roi = l8_swir.where(res_geom_mask)
                    l8_nir_roi = l8_nir.where(res_geom_mask)
                    l8_qa_roi = l8_qa.where(res_geom_mask)
                    x_min, x_max = res_geom.bounds[0],res_geom.bounds[2]
                    y_min, y_max = res_geom.bounds[3],res_geom.bounds[1]

                    l8_green_roi_buffer = l8_green_roi.sel(x=slice(x_min, x_max), y=slice(y_min, y_max))
                    dam_pekel_buffer = clipped.where(dam_geom_mask)
                    pekel_l8_diff = np.array(l8_green_roi_buffer.shape) - np.array(dam_pekel_buffer[0].shape)

                    if pekel_l8_diff.sum !=0:
                        padding_x = pekel_l8_diff[1] * 30
                        padding_y = pekel_l8_diff[0] * 30
                        # l8_green_roi_buffer = l8_green_roi.sel(x=slice(x_min + padding_x, x_max - padding_x), y=slice(y_min - padding_y, y_max + padding_y))
                        # l8_swir_roi_buffer = l8_swir_roi.sel(x=slice(x_min + padding_x, x_max - padding_x), y=slice(y_min - padding_y, y_max + padding_y))
                        # l8_nir_roi_buffer = l8_nir_roi.sel(x=slice(x_min + padding_x, x_max - padding_x), y=slice(y_min - padding_y, y_max + padding_y))
                        # l8_qa_roi_buffer = l8_qa_roi.sel(x=slice(x_min + padding_x, x_max - padding_x), y=slice(y_min - padding_y, y_max + padding_y))
                        l8_green_roi_buffer = l8_green_roi.sel(x=slice(x_min, x_max - padding_x), y=slice(y_min , y_max + padding_y))
                        l8_swir_roi_buffer = l8_swir_roi.sel(x=slice(x_min, x_max - padding_x), y=slice(y_min , y_max + padding_y))
                        l8_nir_roi_buffer = l8_nir_roi.sel(x=slice(x_min, x_max - padding_x), y=slice(y_min , y_max + padding_y))
                        l8_qa_roi_buffer = l8_qa_roi.sel(x=slice(x_min, x_max - padding_x), y=slice(y_min , y_max + padding_y ))
                    else:
                        l8_swir_roi_buffer = l8_swir_roi.sel(x=slice(x_min, x_max), y=slice(y_min, y_max))
                        l8_nir_roi_buffer = l8_nir_roi.sel(x=slice(x_min, x_max), y=slice(y_min, y_max))
                        l8_qa_roi_buffer = l8_qa_roi.sel(x=slice(x_min, x_max), y=slice(y_min, y_max))
                except Exception as e:
                    print(f'Error in reading Landsat-8 data for {dam_name} for date {l8_green.time.values}. Skiping to next date')
                    print(f'Detailed error: {e}')
                    continue
                qa_array = l8_qa_roi_buffer.values.astype(np.uint8)
                cloud_bit = 3
                dilapidated_clouds_bit = 2
                cloud_shadow_bit = 4
                cloud_mask = (np.bitwise_and(qa_array, (1 << cloud_bit)) > 0) | (np.bitwise_and(qa_array, (1 << cloud_shadow_bit)) > 0) | (np.bitwise_and(qa_array, (1 << dilapidated_clouds_bit)) > 0)

                # cloud_mask = np.bitwise_and(qa_array, (1 << cloud_bit)) > 0

                l8_ndwi_roi_buffer = (l8_green_roi_buffer - l8_nir_roi_buffer)/(l8_green_roi_buffer + l8_nir_roi_buffer)
                l8_ndwi = (l8_green - l8_nir)/(l8_green + l8_nir)
                norm = Normalize(vmin = -1, vmax = 1)
                ndwi_threshold = otsu(l8_ndwi)
                l8_water_mk_ndwi = (norm(l8_ndwi_roi_buffer) >= ndwi_threshold).astype(np.uint8)

                #pekel correction
                l8_clouds_mask = cloud_mask.copy()
                l8_water_mk_ndwi_res = l8_water_mk_ndwi.copy()
                pekel_threshold = 10
                # water_area_ndwi = waterArea_correction(res_geom, l8_clouds_mask, l8_water_mk_ndwi_res, pekel_threshold=10, rescale = False, plot = False)
                dam_geom_mask = rio.features.geometry_mask([res_geom], out_shape=clipped.shape[-2:], transform=clipped.rio.transform(), invert=True)

                pekel_water_mk = dam_pekel_buffer[0] > pekel_threshold

                #Cloud masking using Pekel
                #Step1: mask clouds from mndwi mask using cloud mask
                water_mk_less_clouds = l8_water_mk_ndwi_res.copy()
                water_mk_less_clouds[cloud_mask==1] = 0
                #Step2: Obtain pekel data values for areas with clouds
                pekel_inters_clouds = (pekel_water_mk==True).astype(np.uint8)
                pekel_inters_clouds = pekel_inters_clouds.values
                pekel_inters_clouds[cloud_mask == 0] = 0
                #step 3 Add the cloudless mndwi mask with pekel mask for areas with clouds
                water_mk_prob = water_mk_less_clouds.copy()
                water_mk_prob[pekel_inters_clouds == 1] = 1
                #Clean final water mask by removing area with pekel probability equal to 0 and adding areas with prob > 95%
                min_thresh = 5
                pekel_water_mk_95 = dam_pekel_buffer[0] >= 95
                water_mk_prob_clean = water_mk_prob.copy()
                # s2_water_mk_prob_clean[pekel_water_mk == 0] = 0
                water_mk_prob_clean[pekel_water_mk_95 == 1] = 1
                
                #Cloud cover data
                l8_clouds_area = l8_clouds_mask.sum()*(30**2)/1E6
                roi_area = res_geom.area/1E6 #km^2
                l8_perCloudCover = l8_clouds_area/roi_area*100

                water_area_ndwi = water_area(l8_water_mk_ndwi, 30)
                res_area_l8.append({'time': pd.to_datetime(l8_green.time.values, format='%d/%m/%Y'),
                                    'water_area_ndwi': water_area_ndwi/1E6,
                                    'cloud_cover_roi': l8_perCloudCover})
                
                print(f"{counter}. Date: {l8_green.time.values}\n NDWI:{water_area_ndwi/1E6:.2f} km^2")
                counter+=1
            # print(f"Water area computation completed succesfully for time period of {time_of_interest}")
            #Store results in dataframe and export
            res_wa_timeseries_l8 = pd.DataFrame(res_area_l8)
            res_wa_timeseries_l8['time'] = pd.to_datetime(res_wa_timeseries_l8['time'], format='%d/%m/%Y')
            # res_wa_timeseries_l8['dWA_ndwi'] = res_wa_timeseries_l8['water_area_ndwi'].diff()

            res_wa_timeseries_l8.to_csv(output_fp, index = False)
            
        except Exception as e:
            error_dams.append(dam_name)
            counter_dams+=1
            print('Error! Skipping to next dam')
            print(f'Detailed error: {e}')
            continue
        else:
            counter_dams+=1
            dam_finish_time = time.perf_counter() - start_time
            print(f'Time: {dam_finish_time/60} mins')
            print(f"Exported Landsat-8 surface area successfully for {dam_name}\n\n")
            
            
    else:
        print(f'File already exists for {dam_name}. Skipping to next dam\n\n')
        counter_dams+=1
        
end_time = time.perf_counter()
time_taken = end_time - start_time
print(f"Time taken: {time_taken/60} minutes")
