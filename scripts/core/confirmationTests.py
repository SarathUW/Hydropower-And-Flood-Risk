# This script tests 'Likely Flood Inducing' sites for confirmation of the role of reservoir outputs
# Requires RAT3.0 outflow data for each reservoir

#imports
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler
from scipy.stats import pearsonr
from sklearn.metrics import r2_score
from scipy.stats import spearmanr
import warnings
import seaborn as sns

warnings.filterwarnings("ignore")

#reading preliminary resutls
path_prelim = '/prelTests_results.csv' #user needs to provide path to preliminary results
prel_results = pd.read_csv(path_prelim)

ikely_flood_inducing = prel_results[prel_results['Status'] == 'Likely Flood Prone']
likely_protecting = prel_results[(prel_results['Status'] == 'Likely Protected') | (prel_results['Status'] == 'Protected')]
#create a dataset with all remaining points
remaining = prel_results[(prel_results['Status'] != 'Likely Flood Prone') & (prel_results['Status'] != 'Likely Protected') & (prel_results['Status'] != 'Protected')]


# Conducting final analysis for likely flood inducing dams
sum_positive = 0
error_list = []
positive_list = []
results_df = pd.DataFrame(columns=['res_name', 'basin_name', 'grand_id', 'Preliminary_status', 'corr_wet', 'corr_dry','p_value_wet','p_value_dry', 'Confirmatory_status'])

for data in likely_flood_inducing.iloc[:].iterrows():
    print(data[1])
    res_name = data[1]['Study Site']
    basin_name = data[1]['basin_name']
    grand_id = data[1]['GRAND_ID']

    #defining data paths
    dwnst_WA_fp = '' #folder path to study site downstream water area
    outflow_fp = f'' #folder path to study site outflow - RAT3.0 output
    precipitaion_fp = '' #folder path to study site precipitation

    
    try:
        #reading data
        # reading data
        dwnst_WA = pd.read_csv(f'{dwnst_WA_fp}/{res_name}.csv', index_col=0)

        precipitation = pd.read_csv(f'{precipitaion_fp}/{res_name}.csv', index_col=0)
        res_name = res_name.replace(' ', '_')
        outflow = pd.read_csv(f'{outflow_fp}/{grand_id}_{res_name}.csv', index_col=0)

        # convert time to datetime with only date
        dwnst_WA.index = pd.to_datetime(dwnst_WA.index).date
        outflow.index = pd.to_datetime(outflow.index).date
        precipitation.index = pd.to_datetime(precipitation.index).date
        dwnst_WA = dwnst_WA.iloc[::-1]

        #finding dry and wet periods
        precipitation.index = pd.to_datetime(precipitation.index)
        precipitation['month'] = precipitation.index.month
        precipitation['year'] = precipitation.index.year
        precipitation_yearly = precipitation.groupby(['year','month']).sum()
        precip_month = precipitation_yearly.groupby('month').mean()
        print(f"Total Annual Precipitation: {precip_month['MeanPrecipitation_site'].sum()}")

        #using k means clustering to calssify precip into dry and wet periods
        data_for_clustering = precip_month[['MeanPrecipitation_site']]  # Selecting the column to cluster on

        # Normalize data
        scaler = MinMaxScaler()
        data_scaled = scaler.fit_transform(data_for_clustering)

        # Apply K-Means with 2 clusters (for wet and dry)
        kmeans = KMeans(n_clusters=2, random_state=0)
        precip_month['cluster'] = kmeans.fit_predict(data_scaled)

        # Determine which cluster corresponds to "wet" and "dry" based on mean precipitation
        wet_cluster = precip_month.groupby('cluster')['MeanPrecipitation_site'].mean().idxmax()
        precip_month['wet_month'] = precip_month['cluster'] == wet_cluster

        # List wet months
        wet_months = precip_month[precip_month['wet_month']].index.tolist()
        print("Wet months:", wet_months)

        dry_cluster = precip_month.groupby('cluster')['MeanPrecipitation_site'].mean().idxmin()
        precip_month['dry_month'] = precip_month['cluster'] == dry_cluster

        # List dry months
        dry_months = precip_month[precip_month['dry_month']].index.tolist()
        print("Dry months:", dry_months)

        #creating merged dataframe with precip, outflow and water area
        pdf1 = precipitation.copy()
        pdf2 = outflow.copy()
        pdf3 = dwnst_WA.copy()

        pdf3.drop(['cloud_cover_roi','dWA_ndwi'], axis=1, inplace=True)
        pdf1.drop(['MeanPrecipitation_control1','MeanPrecipitation_control2','MeanPrecipitation_control3'], axis=1, inplace=True)


        pdf1['date_integer'] = pdf1.index
        pdf1['date_integer'] = pd.DatetimeIndex(pdf1.index).strftime('%Y%m%d').astype(int)
        pdf2['date_integer'] = pdf2.index
        pdf2['date_integer'] = pd.DatetimeIndex(pdf2.index).strftime('%Y%m%d').astype(int)
        pdf3['date_integer'] = pdf3.index
        pdf3['date_integer'] = pd.DatetimeIndex(pdf3.index).strftime('%Y%m%d').astype(int)

        pdf1 = pdf1.drop_duplicates(subset = ['date_integer'], keep='first')
        pdf2 = pdf2.drop_duplicates(subset = ['date_integer'], keep='first')
        pdf3 = pdf3.drop_duplicates(subset = ['date_integer'], keep='first')


        # pdf2 = pdf2.reindex(pdf1.index)
        # pdf3 = pdf3.reindex(pdf1.index)
        # pdf2['outflow (m3/d)'] = pdf2['outflow (m3/d)'].interpolate()
        # pdf3['water_area_ndwi'] = pdf3['water_area_ndwi'].interpolate()

        pdf2 = pdf2.reindex(pdf1.index)
        pdf3 = pdf3.reindex(pdf1.index)
        pdf2['outflow (m3/d)'] = pdf2['outflow (m3/d)'].interpolate(method = 'time')
        pdf3['water_area_ndwi'] = pdf3['water_area_ndwi'].interpolate(method = 'time')

        pdf1.drop('date_integer', axis = 1, inplace = True)
        pdf2.drop('date_integer', axis = 1, inplace = True)
        pdf3.drop('date_integer', axis = 1, inplace = True)
        # Assuming pdf1 and pdf2 are your DataFrames
        merged = pdf1.merge(pdf2, left_index=True, right_index=True, how='inner').merge(pdf3, left_index=True, right_index=True, how='inner')
        merged_scaled = scaler.fit_transform(merged)
        merged_scaled = pd.DataFrame(merged_scaled, columns=merged.columns, index=merged.index)
        merged_scaled['month'] = merged['month']
        #convert wet months to int
        wet_months = [int(x) for x in wet_months]

        #grouping data
        merged_scaled.index = pd.to_datetime(merged_scaled.index)
        merged_wet = merged_scaled[merged_scaled['month'].isin(wet_months)]
        merged_dry = merged_scaled[~merged_scaled['month'].isin(wet_months)]
        merged_wet = merged_wet.dropna()
        merged_dry = merged_dry.dropna()

        max_waterArea_index_wet = merged_wet.groupby(merged_wet.index.year)['water_area_ndwi'].idxmax()
        merged_wet_maxWaterArea = merged_wet.loc[max_waterArea_index_wet]
        # max_waterArea_index_dry = merged_dry.groupby(merged_dry.index.year)['water_area_ndwi'].idxmax()
        max_waterArea_index_dry = merged_dry.groupby(merged_dry.index.year)['water_area_ndwi'].apply(lambda x: (x - x.median()).abs().idxmin())

        

        merged_dry_maxWaterArea = merged_dry.loc[max_waterArea_index_dry]
        merged_wet_maxWaterArea = merged_wet_maxWaterArea.dropna()
        merged_dry_maxWaterArea = merged_dry_maxWaterArea.dropna()

        #Computing correlation, r2 and spearman correlation
        wet_maxWaterArea_corr = pearsonr(merged_wet_maxWaterArea['outflow (m3/d)'], merged_wet_maxWaterArea['water_area_ndwi'])
        wet_maxWaterArea_r2 = r2_score(merged_wet_maxWaterArea['outflow (m3/d)'], merged_wet_maxWaterArea['water_area_ndwi'])
        wet_maxWaterArea_spearman = spearmanr(merged_wet_maxWaterArea['outflow (m3/d)'], merged_wet_maxWaterArea['water_area_ndwi'])
        wet_maxWaterArea_pValue = wet_maxWaterArea_spearman[1]

        dry_maxWaterArea_corr = pearsonr(merged_dry_maxWaterArea['outflow (m3/d)'], merged_dry_maxWaterArea['water_area_ndwi'])
        dry_maxWaterArea_r2 = r2_score(merged_dry_maxWaterArea['outflow (m3/d)'], merged_dry_maxWaterArea['water_area_ndwi'])
        dry_maxWaterArea_spearman = spearmanr(merged_dry_maxWaterArea['outflow (m3/d)'], merged_dry_maxWaterArea['water_area_ndwi'])
        dry_maxWaterArea_pValue = dry_maxWaterArea_spearman[1]

        print(f'Wet Period Stats:\n Correlation: {wet_maxWaterArea_corr[0]:.2f}, R2: {wet_maxWaterArea_r2:.2f}, Spearman: {wet_maxWaterArea_spearman[0]:.2f}')
        print(f'Dry Period Stats:\n Correlation: {dry_maxWaterArea_corr[0]:.2f}, R2: {dry_maxWaterArea_r2:.2f}, Spearman: {dry_maxWaterArea_spearman[0]:.2f}')

        if ((wet_maxWaterArea_spearman[0]) > 0 and (wet_maxWaterArea_spearman[0] > dry_maxWaterArea_spearman[0])): #and abs(wet_maxWaterArea_spearman[0] - dry_maxWaterArea_spearman[0]) > 0.3:
            if abs(wet_maxWaterArea_spearman[0] - dry_maxWaterArea_spearman[0]) > 0.2:
                confirmatory_status = 'Likely Flood Inducing (HC)'
        else:
                confirmatory_status = 'Likely Flood Inducing'
        # else:
        #     confirmatory_status = 'Ambiguous'
            
        # sum_positive += 1
        # positive_list.append(res_name)
        
        results_df = pd.concat([results_df, pd.DataFrame({'res_name':res_name, 'basin_name':basin_name, 'grand_id':grand_id, 'Preliminary_status':'Likely Flood Prone', 'corr_wet':wet_maxWaterArea_spearman[0], 'corr_dry':dry_maxWaterArea_spearman[0],'p_value_wet': wet_maxWaterArea_pValue,'p_value_dry': dry_maxWaterArea_pValue, 'Confirmatory_status':confirmatory_status}, index=[0])], ignore_index=True)


    except:
        error_list.append(res_name)
        confirmatory_status = 'Likely Flood Inducing'
        results_df = pd.concat([results_df, pd.DataFrame({'res_name':res_name, 'basin_name':basin_name, 'grand_id':grand_id, 'Preliminary_status':'Likely Flood Prone', 'corr_wet':-9999, 'corr_dry':-9999,'p_value_wet': -9999,'p_value_dry': -9999, 'Confirmatory_status':confirmatory_status}, index=[0])], ignore_index=True)

        continue

    

print(f"Number of positive results: {sum_positive} / {len(likely_flood_inducing)}")
print(f"Positive results: {positive_list}")
print(f"Error results: {error_list}")