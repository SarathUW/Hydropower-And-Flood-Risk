#This script processes GlobPop dataset for study site locations
# and computes yearly population dataset

dam_data = gpd.read_file('')

dam_floodInducing = dam_data[dam_data['Confirmatory_status'] == 'Likely Flood Protecting']
dam_protected = dam_data[dam_data['Confirmatory_status'] == 'Likely Flood Protecting']

output_path = ''
pop_data_folder = ''
pop_data_format = 'GlobPop_{}.tiff'
for  _,row in tqdm(dam_floodInducing.iterrows(), total=dam_floodInducing.shape[0]):
    dam_id = row['GRAND_ID']
    dam_name = row['DAM_NAME']
    print(dam_name)
    
    pop_df = pd.DataFrame(columns=['year', 'total_pop(M)'])
    for date in range(1990, 2021):

        pop_data_path = f'{pop_data_folder}/{pop_data_format.format(date)}'

        ##creating 1degree (~112km) buffer about dam geometry
        dam_geom = row['geometry']
        geom_buffer = dam_geom.buffer(1)

        if os.path.exists(pop_data_path):
            pop_data = rioxarray.open_rasterio(pop_data_path, masked=True)
            pop_clipped = pop_data.rio.clip([geom_buffer], crs=dam_floodInducing.crs, drop=True)

            total_pop = pop_clipped.sum().values/1e6
            pop_df = pd.concat([pop_df, pd.DataFrame({'year': [date], 'total_pop(M)': [total_pop]})])

        print(date, total_pop)
    
    #saving data
    pop_df.to_csv(f'{output_path}/{dam_name}.csv', index=False)