#This script smooths satellite data derived surface area using weighted average 
#with cloud cover as a factor

import numpy as np
import geopandas as gpd
import os
import pandas as pd

def weighted_moving_average(data, weights, window_size):
    if window_size % 2 == 0 or window_size < 1:
        raise ValueError("Window size must be an odd positive integer.")

    data = np.array(data)
    weights = np.array(weights)

    if data.shape != weights.shape:
        raise ValueError("Data and weights must have the same shape.")

    half_window = window_size // 2
    smoothed_data = np.zeros_like(data)

    for i in range(len(data)):
        start = max(0, i - half_window)
        end = min(len(data), i + half_window + 1)

        weighted_values = data[start:end] * weights[start:end]

        # Calculate the weighted moving average
        smoothed_data[i] = np.sum(weighted_values) / np.sum(weights[start:end])

    return smoothed_data


counter = 1
error_dams = []
dams_ROI_fp = '' #shapefile with study site data
dams_ROI = gpd.read_file(dams_ROI_fp)
num_dams = len(dams_ROI['DAM_NAME'])
for dam_name in dams_ROI['DAM_NAME'][102:103]:
    try:
        print(f'{counter}/{num_dams}. {dam_name}')
        input_fp = f'/SA_landsat/{dam_name}.csv'
        output_fp = f'/SA_smoothened/{dam_name}.csv'
        if not os.path.exists(output_fp):
            sa_data = pd.read_csv(input_fp)
            sa_data['area'] = weighted_moving_average(sa_data['water_area_ndwi'], weights = (101-sa_data['cloud_cover_roi']),window_size=9)

        else:
            print(f'{dam_name} already processed')
            continue


    except Exception as e:
        print(f'Error: {e}')
        error_dams.append(dam_name)
    else:
        sa_data.to_csv(output_fp, index=False)
    counter += 1  
print(f'Error dams: {error_dams}')   