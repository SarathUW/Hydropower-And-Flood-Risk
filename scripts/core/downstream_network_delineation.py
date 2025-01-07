# This script identifies the downstream stream 
# for a given dam/site location using HydroRivers data

import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

#user data
rivers_fp = '' #provide the hydrorivers dataset shapefile clipped to a region large than the area of interest
dams_fp = '' #shapefile containing study site locations as geometry
output_folder = ''

riverNet = gpd.read_file(rivers_fp)
dams_gpd = gpd.read_file(dams_fp)


errorList = []
counter = 1
print('Creating river network for dams in the dataset')
for dam in dams_gpd.iterrows():
    print(f'Dam number: {counter}. {dam[1]["DAM_NAME"]}') 

    output_fn = f'{output_folder}/{dam[1]["DAM_NAME"]}_riverNet.geojson'

    if os.path.exists(output_fn):
        print('River Network file already exists. Skipping. \n')
        counter += 1
        continue
    else:
        dam_loc = [dam[1]['LAT_DD'],dam[1]['LONG_DD']]
        dam_point = Point(dam_loc[1],dam_loc[0])

        gdf_lines = riverNet
        point = dam_point

        buffer_val = 0.002 #degrees
        dam_point_buffered = dam_point.buffer(buffer_val)

        isOnNetwork = False
        for idx,row in riverNet.iterrows():
            if dam_point_buffered.intersects(row.geometry):
                print('dam lies on network')
                isOnNetwork = True
                damNetwork_ID = row['HYRIV_ID']
                G = nx.DiGraph()
        
        if isOnNetwork:
            for idx, row in riverNet.iterrows():
                G.add_node(row['HYRIV_ID'])
                if not pd.isnull(row['NEXT_DOWN']):
                    G.add_edge(row['HYRIV_ID'], int(row['NEXT_DOWN']))
        
            start_node = damNetwork_ID

            # Find the connected network starting from the chosen point
            connected_network = nx.descendants(G, start_node)

            # Subset the original DataFrame based on the connected network
            selected_rivers = riverNet[riverNet['HYRIV_ID'].isin(connected_network)]

            # # Plot the selected rivers
            # selected_rivers.plot()
            # plt.show()

            #saving dam network to disk
            print('Saving network to file. \n')
            selected_rivers.to_file(output_fn, driver='GeoJSON')
        else:
            print('dam not on network. Try changing buffer value. \n')
            errorList.append(dam[1]['DAM_NAME'])

    counter += 1
print(f'Completed creating river networks for {counter} dams in the dataset. Errors: {errorList}')