# This script generates similary scores between study sites and control sites 
# to identify top 3 control sites for each study site
# The data is then saved as a .pickle file

import xarray as xr
import rioxarray as rxr
import geopandas as gpd
import os
import warnings
import pandas as pd
import pickle


warnings.filterwarnings("ignore")

#Pre-requisite data
studySites_dataset = pd.read_csv('')
controlSites_dataset = pd.read_csv('')
distances_df = pd.read_csv('', index_col=0)

#iterate over every study site and compute the similarity score
# similarity_scores = pd.DataFrame(index=studySites_dataset['Dam Name'], columns=controlSites_dataset.ControlSite.astype(str))
similarity_scores = pd.DataFrame(index=controlSites_dataset.ControlSite.astype(str), columns=studySites_dataset['Dam Name'])
slope_weight = 0.2
# porosity_weight = 0.2
precip_weight = 0.5
distance_weight = 0.2
urban_weight = 0.1

site_minSlope = studySites_dataset['Mean Slope'].min()
site_maxSlope = studySites_dataset['Mean Slope'].max()
# site_minPorosity = studySites_dataset['Mean Porosity'].min()
# site_maxPorosity = studySites_dataset['Mean Porosity'].max()
site_minPrecip = studySites_dataset['Mean Precipitation'].min()
site_maxPrecip = studySites_dataset['Mean Precipitation'].max()
site_minUrban = studySites_dataset['Percentage Urban'].min()
site_maxUrban = studySites_dataset['Percentage Urban'].max()
max_distance = distances_df.max().max()


for site_index, site in studySites_dataset.iterrows():
    site_name = site['Dam Name']
    site_slope = site['Mean Slope']
    site_porosity = site['Mean Porosity']
    site_precip = site['Mean Precipitation']
    site_urban = site['Percentage Urban']
    print(f'Computing similarity scores for {site_name}')
    for control_idx, control_site in controlSites_dataset.iterrows():
        cs_name = str(int(control_site['ControlSite']))
        cs_slope = control_site['Mean Slope']
        cs_porosity = control_site['Mean Porosity']
        cs_precip = control_site['Mean Precipitation']
        cs_urban = control_site['Percentage Urban']

        # compute the similarity score
        slope_score = 1 - abs(site_slope - cs_slope)/(site_maxSlope - site_minSlope)
        porosity_score = 1 - abs(site_porosity - cs_porosity)/(site_maxPorosity - site_minPorosity)
        precip_score = 1 - abs(site_precip - cs_precip)/(site_maxPrecip - site_minPrecip)
        distance_score = 1 - distances_df.loc[site_name, cs_name]/max_distance
        urban_score = 1 - abs(site_urban - cs_urban)/(site_maxUrban - site_minUrban)
        
        # similarity_score = slope_weight*slope_score + porosity_weight*porosity_score + precip_weight*precip_score + distance_weight*distance_score 
        similarity_score = slope_weight*slope_score + precip_weight*precip_score + distance_weight*distance_score + urban_weight*urban_score   
        print(f'slope_score: {slope_score}, porosity_score: {porosity_score}, precip_score: {precip_score}, distance_score: {distance_score}, urban_score: {urban_score}')
        print(f'{site_name} - {cs_name}: {similarity_score}')
        similarity_scores.loc[cs_name,site_name] = similarity_score      

similarity_scores.to_csv('', index=True)


top3_simScore_controlSites = {}
for site in similarity_score.columns:
    print(f'Study Site: {site}')
    control_site_simScore = similarity_score[site]
    # ids of top 3 control sites
    top3 = control_site_simScore.nlargest(3).index.values
    print(site, top3)
    top3_simScore_controlSites[site] = top3

# save the dictionary to a file using pickle
with open('/top3_simScore_controlSites.pkl', 'wb') as f:
    pickle.dump(top3_simScore_controlSites, f)