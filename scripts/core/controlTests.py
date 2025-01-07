# This script contains various functions used to perform 
# control site tests for Intitial Flood Risk Assessment

import pandas as pd
import pickle
import warnings
import scipy.stats as stats
import seaborn as sns
from scikit_posthocs import posthoc_dunn
from scipy.stats import kruskal
from tqdm import tqdm
import matplotlib.pyplot as plt
import altair as alt


warnings.filterwarnings("ignore")

#user data
res_fp = ''
studySite_precipitaiton_fp = ''
controlSite_precipitaiton_fp = ''
studySite_waterArea_fp = ''
controlSite_waterArea_fp = ''

similarity_score = ''

with open('/water3/saraths/Research_Files/Study2/ControlTests/datasets/top3_simScore_controlSites.pkl', 'rb') as f:
    top3_simScore_controlSites = pickle.load(f)


def dataInterpolate(data_precip, data_site, data_control1, data_control2, data_control3):
    """
    Interpolates and normalizes water area and precipitation data for a study site and its control sites.

    Parameters:
    data_precip (DataFrame): DataFrame containing precipitation data with columns 'Date' and 'MeanPrecipitation_site'.
    data_site (DataFrame): DataFrame for the study site containing 'time', 'water_area_ndwi', and 'cloud_cover_roi'.
    data_control1 (DataFrame): DataFrame for the first control site containing 'time', 'water_area_ndwi', and 'cloud_cover_roi'.
    data_control2 (DataFrame): DataFrame for the second control site containing 'time', 'water_area_ndwi', and 'cloud_cover_roi'.
    data_control3 (DataFrame): DataFrame for the third control site containing 'time', 'water_area_ndwi', and 'cloud_cover_roi'.

    Returns:
    DataFrame: Merged and normalized DataFrame that includes interpolated water area and normalized precipitation data
    for the study site and control sites.
    """

    data_precip['time'] = pd.to_datetime(data_precip['Date'])
    data_precip['date'] = data_precip['time'].dt.date
    data_site['time'] = pd.to_datetime(data_site['time'])
    data_site['date'] = data_site['time'].dt.date
    data_control1['time'] = pd.to_datetime(data_control1['time'])
    data_control1['date'] = data_control1['time'].dt.date
    data_control2['time'] = pd.to_datetime(data_control2['time'])
    data_control2['date'] = data_control2['time'].dt.date
    data_control3['time'] = pd.to_datetime(data_control3['time'])
    data_control3['date'] = data_control3['time'].dt.date

     #Setting date as index and creating copies for further manipulation
    pdf1 = data_precip.copy()
    pdf2 = data_site.copy()
    pdf3 = data_control1.copy()
    pdf4 = data_control2.copy()
    pdf5 = data_control3.copy()

    pdf1 = pdf1.set_index('date')
    pdf2 = pdf2.set_index('date')
    pdf3 = pdf3.set_index('date')
    pdf4 = pdf4.set_index('date')
    pdf5 = pdf5.set_index('date')

    #dropping unwanted rows
    pdf2.drop('dWA_ndwi', axis = 1, inplace = True)
    pdf3.drop('dWA_ndwi', axis = 1, inplace = True)
    pdf4.drop('dWA_ndwi', axis = 1, inplace = True)
    pdf5.drop('dWA_ndwi', axis = 1, inplace = True)

    pdf2.drop('cloud_cover_roi', axis = 1, inplace = True)
    pdf3.drop('cloud_cover_roi', axis = 1, inplace = True)
    pdf4.drop('cloud_cover_roi', axis = 1, inplace = True)
    pdf5.drop('cloud_cover_roi', axis = 1, inplace = True)

    pdf1['date_integer1'] = pdf1.index
    pdf1['date_integer1'] = pd.DatetimeIndex(pdf1.index).strftime('%Y%m%d').astype(int)
    pdf2['date_integer2'] = pdf2.index
    pdf2['date_integer2'] = pd.DatetimeIndex(pdf2.index).strftime('%Y%m%d').astype(int)
    pdf3['date_integer3'] = pdf3.index
    pdf3['date_integer3'] = pd.DatetimeIndex(pdf3.index).strftime('%Y%m%d').astype(int)
    pdf4['date_integer4'] = pdf4.index
    pdf4['date_integer4'] = pd.DatetimeIndex(pdf4.index).strftime('%Y%m%d').astype(int)
    pdf5['date_integer5'] = pdf5.index
    pdf5['date_integer5'] = pd.DatetimeIndex(pdf5.index).strftime('%Y%m%d').astype(int)

    pdf1 = pdf1.drop_duplicates(subset = ['date_integer1'], keep='first')
    pdf2 = pdf2.drop_duplicates(subset = ['date_integer2'], keep='first')
    pdf3 = pdf3.drop_duplicates(subset = ['date_integer3'], keep='first')
    pdf4 = pdf4.drop_duplicates(subset = ['date_integer4'], keep='first')
    pdf5 = pdf5.drop_duplicates(subset = ['date_integer5'], keep='first')

    pdf2 = pdf2.reindex(pdf1.index)
    pdf2['water_area_ndwi_dam'] = pdf2['water_area_ndwi'].interpolate()
    pdf3 = pdf3.reindex(pdf1.index)
    pdf3['water_area_ndwi_control1'] = pdf3['water_area_ndwi'].interpolate()
    pdf4 = pdf4.reindex(pdf1.index)
    pdf4['water_area_ndwi_control2'] = pdf4['water_area_ndwi'].interpolate()
    pdf5 = pdf5.reindex(pdf1.index)
    pdf5['water_area_ndwi_control3'] = pdf5['water_area_ndwi'].interpolate()

  
    pdf2.drop('time', axis = 1, inplace = True)
    pdf2['date_integer'] = pd.DatetimeIndex(pdf2.index).strftime('%Y%m%d').astype(int)
    pdf3.drop('time', axis = 1, inplace = True)
    pdf3['date_integer'] = pd.DatetimeIndex(pdf3.index).strftime('%Y%m%d').astype(int)
    pdf4.drop('time', axis = 1, inplace = True)
    pdf4['date_integer'] = pd.DatetimeIndex(pdf4.index).strftime('%Y%m%d').astype(int)
    pdf5.drop('time', axis = 1, inplace = True)
    pdf5['date_integer'] = pd.DatetimeIndex(pdf5.index).strftime('%Y%m%d').astype(int)


    #drop the water_area_ndwi column
    pdf2.drop('water_area_ndwi', axis = 1, inplace = True)
    pdf3.drop('water_area_ndwi', axis = 1, inplace = True)
    pdf4.drop('water_area_ndwi', axis = 1, inplace = True)
    pdf5.drop('water_area_ndwi', axis = 1, inplace = True) 

    #drop date_integer column
    pdf1.drop('date_integer1', axis = 1, inplace = True)
    pdf2.drop(['date_integer','date_integer2'], axis = 1, inplace = True)
    pdf3.drop('date_integer3', axis = 1, inplace = True)
    pdf4.drop('date_integer4', axis = 1, inplace = True)
    pdf5.drop('date_integer5', axis = 1, inplace = True)

    merged = pdf1.merge(pdf2, on = 'date', how = 'inner').merge(pdf3, on = 'date', how = 'inner').merge(pdf4, on = 'date', how = 'inner').merge(pdf5, on = 'date', how = 'inner')
    merged = merged.drop(index = merged.index[0:10])

    # min max normalising the water_area_ndwi columns
    merged['water_area_ndwi_control1_norm'] = (merged['water_area_ndwi_control1'] - merged['water_area_ndwi_control1'].min())/(merged['water_area_ndwi_control1'].max() - merged['water_area_ndwi_control1'].min())
    merged['water_area_ndwi_control2_norm'] = (merged['water_area_ndwi_control2'] - merged['water_area_ndwi_control2'].min())/(merged['water_area_ndwi_control2'].max() - merged['water_area_ndwi_control2'].min())
    merged['water_area_ndwi_control3_norm'] = (merged['water_area_ndwi_control3'] - merged['water_area_ndwi_control3'].min())/(merged['water_area_ndwi_control3'].max() - merged['water_area_ndwi_control3'].min())
    merged['water_area_ndwi_dam_norm'] = (merged['water_area_ndwi_dam'] - merged['water_area_ndwi_dam'].min())/(merged['water_area_ndwi_dam'].max() - merged['water_area_ndwi_dam'].min())

    # min max normalising the precipitation columns
    merged['MeanPrecipitation_site_norm'] = (merged['MeanPrecipitation_site'] - merged['MeanPrecipitation_site'].min())/(merged['MeanPrecipitation_site'].max() - merged['MeanPrecipitation_site'].min())
    merged['MeanPrecipitation_control1_norm'] = (merged['MeanPrecipitation_control1'] - merged['MeanPrecipitation_control1'].min())/(merged['MeanPrecipitation_control1'].max() - merged['MeanPrecipitation_control1'].min())
    merged['MeanPrecipitation_control2_norm'] = (merged['MeanPrecipitation_control2'] - merged['MeanPrecipitation_control2'].min())/(merged['MeanPrecipitation_control2'].max() - merged['MeanPrecipitation_control2'].min())
    merged['MeanPrecipitation_control3_norm'] = (merged['MeanPrecipitation_control3'] - merged['MeanPrecipitation_control3'].min())/(merged['MeanPrecipitation_control3'].max() - merged['MeanPrecipitation_control3'].min())


    return merged

def mann_whitney_u_test(study_data, control_data, control_name):
    """
    Conducts a two-sided Mann-Whitney U test to compare a study data set with a control data set.

    Parameters
    ----------
    study_data : array_like
        The array of values for the study data set.
    control_data : array_like
        The array of values for the control data set.
    control_name : str
        The name of the control data set, used to identify the test results.

    Returns
    -------
    control_name : str
        The name of the control data set.
    p_value : float
        The p-value from the Mann-Whitney U test.
    """
    u_stat, p_value = stats.mannwhitneyu(study_data, control_data, alternative='two-sided')
    return control_name, p_value

def interpret_combined_score(test_results):
    """
    Interprets the results of the three statistical tests as a single score

    Parameters
    ----------
    test_results : dict
        A dictionary with the results of the three statistical tests. The keys should be the names of the tests and the values should be integers indicating the outcome of the test (0 or 1).

    Returns
    -------
    score : int
        The combined score of the three tests
    status : str
        The status of the dam based on the combined score
    """
    score = sum(test_results.values())
    status = ''
    if score == 2:
        status = 'Flood Prone'
        return(score, status)
    elif score in [3,4, 5]:
        status = 'Likely Flood Prone'
        return(score, status)
    elif score == 6:
        status = 'Ambiguous'
        return(score, status)
    elif score in [7,8, 9]:
        status = 'Likely Protected'
        return(score, status)
    elif score == 10:
        status = 'Protected'
        return(score, status)



##  group run of control - study site tests
output_df = pd.DataFrame(columns = ['Study Site', 'Test1', 'Test2', 'Combined Score', 'Status'])
error_list = []
for key, value in tqdm(top3_simScore_controlSites.items(), desc = 'Processing study sites'):
    print(f'Study Site: {key}')
    print(f'Top 3 Control Sites: {value}')
    print('\n')

    dam_name = key
    control1 = top3_simScore_controlSites[dam_name][0]
    control2 = top3_simScore_controlSites[dam_name][1]
    control3 = top3_simScore_controlSites[dam_name][2]

    try:
        studySite_precip_data = pd.read_csv(studySite_precipitaiton_fp + '/' + dam_name + '.csv')
        studySite_waterArea = pd.read_csv(studySite_waterArea_fp + '/' + dam_name + '.csv')
        control1_waterArea = pd.read_csv(controlSite_waterArea_fp + '/' + str(control1) + '.csv')
        control2_waterArea = pd.read_csv(controlSite_waterArea_fp + '/' + str(control2) + '.csv')
        control3_waterArea = pd.read_csv(controlSite_waterArea_fp + '/' + str(control3) + '.csv')

        combined_data = dataInterpolate(studySite_precip_data, studySite_waterArea, control1_waterArea, control2_waterArea, control3_waterArea)
        
        #Test 1 - Flood frequency analysis
        # creating three datasets for study site and 3 control sites
        study_site_data = combined_data[['MeanPrecipitation_site_norm', 'water_area_ndwi_dam_norm']]
        control1_data = combined_data[['MeanPrecipitation_control1_norm', 'water_area_ndwi_control1_norm']]
        control2_data = combined_data[['MeanPrecipitation_control2_norm', 'water_area_ndwi_control2_norm']]
        control3_data = combined_data[['MeanPrecipitation_control3_norm', 'water_area_ndwi_control3_norm']]

        #Step 1 - creating flood dataset
        high_percentile_threshold = 0.8 # 99th percentile
        studySite_precipitation_threshold = study_site_data['MeanPrecipitation_site_norm'].quantile(high_percentile_threshold)
        studySite_waterArea_threshold = study_site_data['water_area_ndwi_dam_norm'].quantile(high_percentile_threshold)
        # Filter data for high water area points
        studySite_flood_df = study_site_data[
            (study_site_data['MeanPrecipitation_site_norm'] >= studySite_precipitation_threshold) &
            (study_site_data['water_area_ndwi_dam_norm'] >= studySite_waterArea_threshold)
        ]
        studySite_flood_df_test2 = study_site_data[study_site_data['MeanPrecipitation_site_norm'] >= studySite_precipitation_threshold]
        studySite_flood_df_test2 = studySite_flood_df_test2.dropna()
        # Add a column to indicate flood events
        studySite_flood_df['Flood'] = True
        #remove all nan values from the dataset
        studySite_flood_df = studySite_flood_df.dropna()

        ##test 1 - flood frequency analysis
        #test results value = 1 - study site is a flood prone site statistically
        #test results value = 2 - study site might be a flood prone site but not statistically significant
        #test results value = 3 - study site is neither a flood prone site nor a protected site
        #test results value = 4 - study site might be a protected site but not statistically significant 
        #test results value = 5 - study site is a protected site statistically
        test_results = {}

        # create year column from date
        studySite_flood_df['Year'] = pd.DatetimeIndex(studySite_flood_df.index).year
        # Frequency of flood occurrences
        studySite_flood_frequency = studySite_flood_df.groupby(['Year']).size().reset_index(name='Flood_Count')
        studySite_average_flood_frequency = int(studySite_flood_frequency['Flood_Count'].mean())

        # Repeat the same for control sites
        control1_precipitation_threshold = control1_data['MeanPrecipitation_control1_norm'].quantile(high_percentile_threshold)
        control1_waterArea_threshold = control1_data['water_area_ndwi_control1_norm'].quantile(high_percentile_threshold)

        control1_flood_df_test2 = control1_data[control1_data['MeanPrecipitation_control1_norm'] >= control1_precipitation_threshold]
        control1_flood_df = control1_data[
            (control1_data['MeanPrecipitation_control1_norm'] >= control1_precipitation_threshold) &
            (control1_data['water_area_ndwi_control1_norm'] >= control1_waterArea_threshold)
        ]

        control1_flood_df['Flood'] = True
        #remove all nan values from the dataset
        control1_flood_df = control1_flood_df.dropna()
        control1_flood_df_test2 = control1_flood_df_test2.dropna()

        control1_flood_df['Year'] = pd.DatetimeIndex(control1_flood_df.index).year
        control1_flood_frequency = control1_flood_df.groupby(['Year']).size().reset_index(name='Flood_Count')
        control1_average_flood_frequency = int(control1_flood_frequency['Flood_Count'].mean())

        control2_precipitation_threshold = control2_data['MeanPrecipitation_control2_norm'].quantile(high_percentile_threshold)
        control2_waterArea_threshold = control2_data['water_area_ndwi_control2_norm'].quantile(high_percentile_threshold)

        control2_flood_df_test2 = control2_data[control2_data['MeanPrecipitation_control2_norm'] >= control2_precipitation_threshold]
        control2_flood_df = control2_data[
            (control2_data['MeanPrecipitation_control2_norm'] >= control2_precipitation_threshold) &
            (control2_data['water_area_ndwi_control2_norm'] >= control2_waterArea_threshold)
        ]
        control2_flood_df['Flood'] = True
        #remove all nan values from the dataset
        control2_flood_df = control2_flood_df.dropna()
        control2_flood_df_test2 = control2_flood_df_test2.dropna()


        control2_flood_df['Year'] = pd.DatetimeIndex(control2_flood_df.index).year
        control2_flood_frequency = control2_flood_df.groupby(['Year']).size().reset_index(name='Flood_Count')
        control2_average_flood_frequency = int(control2_flood_frequency['Flood_Count'].mean())

        control3_precipitation_threshold = control3_data['MeanPrecipitation_control3_norm'].quantile(high_percentile_threshold)
        control3_waterArea_threshold = control3_data['water_area_ndwi_control3_norm'].quantile(high_percentile_threshold)

        control3_flood_df_test2 = control3_data[control3_data['MeanPrecipitation_control3_norm'] >= control3_precipitation_threshold]
        control3_flood_df = control3_data[
            (control3_data['MeanPrecipitation_control3_norm'] >= control3_precipitation_threshold) &
            (control3_data['water_area_ndwi_control3_norm'] >= control3_waterArea_threshold)
        ]
        control3_flood_df['Flood'] = True
        #remove all nan values from the dataset
        control3_flood_df = control3_flood_df.dropna()
        control3_flood_df_test2 = control3_flood_df_test2.dropna()

        control3_flood_df['Year'] = pd.DatetimeIndex(control3_flood_df.index).year
        control3_flood_frequency = control3_flood_df.groupby(['Year']).size().reset_index(name='Flood_Count')
        control3_average_flood_frequency = int(control3_flood_frequency['Flood_Count'].mean())

        #dictionary mapping the site and their flood dataset variable names
        site_flood_dict = {
            'StudySite': studySite_flood_df,
            'Control1': control1_flood_df,
            'Control2': control2_flood_df,
            'Control3': control3_flood_df
        }

        #create a dictionary of flood frequency datasets
        flood_frequency_dict = {
            'StudySite': studySite_flood_frequency,
            'Control1': control1_flood_frequency,
            'Control2': control2_flood_frequency,
            'Control3': control3_flood_frequency
        }
        #create a dictionary of study_sites, control sites and their average flood frequency
        average_flood_frequency_dict = {
            'StudySite': studySite_average_flood_frequency,
            'Control1': control1_average_flood_frequency,
            'Control2': control2_average_flood_frequency,
            'Control3': control3_average_flood_frequency
        }
        # sort the dictionary by flood frequency
        sorted_flood_frequency_dict = dict(sorted(average_flood_frequency_dict.items(), key=lambda item: item[1]))

        #if study site has the highest flood frequency, then it is a potential flood site and we need to perform 
        #Mann-Whitney U test to check if the flood frequency is significantly different from the second highest flood frequency control site
        print(sorted_flood_frequency_dict)
        if list(sorted_flood_frequency_dict.keys())[-1] == 'StudySite':
            key = list(sorted_flood_frequency_dict.keys())[-2]
            p_values = mann_whitney_u_test(studySite_flood_frequency['Flood_Count'], flood_frequency_dict[key]['Flood_Count'], key)
            p_values = p_values[1]
            print(p_values)
            if p_values < 0.05:
                print(f'{dam_name} is a flood prone site statistically based on flood frequency analysis using ranking and Mann-Whitney U test')
                test_results['Test1:'] = 1
            else:
                print(f'{dam_name} might be a flood prone site but it is not statistically significant based on flood frequency analysis using ranking and Mann-Whitney U test')
                test_results['Test1:'] = 2

        # if study site has the lowest flood frequency, then it might be a protected site and we need to perform
        # Mann-Whitney U test to check if the flood frequency is significantly different from the second lowest flood frequency control site

        elif list(sorted_flood_frequency_dict.keys())[0] == 'StudySite':
            key = list(sorted_flood_frequency_dict.keys())[1]
            p_values = mann_whitney_u_test(studySite_flood_frequency['Flood_Count'], flood_frequency_dict[key]['Flood_Count'], key)
            p_values = p_values[1]

            if p_values < 0.05:
                print(f'{dam_name} is a protected site statistically based on flood frequency analysis using ranking and Mann-Whitney U test')
                test_results['Test1:'] = 5

            else:
                print(f'{dam_name} might be a protected site but it is not statistically significant based on flood frequency analysis using ranking and Mann-Whitney U test')
                test_results['Test1:'] = 4

        else:
            print(f'{dam_name} is neither a flood prone site nor a protected site based on flood frequency analysis using ranking and Mann-Whitney U test')
            test_results['Test1:'] = 3

        ##test 2 - Flood intensity analysis
        data_test2 = [
            studySite_flood_df_test2['water_area_ndwi_dam_norm'],
            control1_flood_df_test2['water_area_ndwi_control1_norm'],
            control2_flood_df_test2['water_area_ndwi_control2_norm'],
            control3_flood_df_test2['water_area_ndwi_control3_norm']
        ]

        # Combine all data into a single DataFrame
        all_data = pd.DataFrame({
            'FloodIntensity': pd.concat(data_test2).reset_index(drop=True),
            'Group': (
                ['StudySite'] * len(studySite_flood_df_test2) +
                ['Control1'] * len(control1_flood_df_test2) +
                ['Control2'] * len(control2_flood_df_test2) +
                ['Control3'] * len(control3_flood_df_test2)
            )
        })

        # Calculate and print medians
        medians = all_data.groupby('Group').median()
        sorted_medians = medians['FloodIntensity'].sort_values(ascending=True)
        print(sorted_medians)

        # Perform Kruskal-Wallis test
        stat, p_value_kruskal = kruskal(*data_test2)
        print(f'Kruskal-Wallis Test: H-statistic = {stat}, p-value = {p_value_kruskal}')

        # Perform Dunn's post-hoc test
        posthoc_results = posthoc_dunn(all_data, val_col='FloodIntensity', group_col='Group', p_adjust='bonferroni')
        print('Dunn\'s Post-hoc Test Results:')
        print(posthoc_results)


        post_hoc_study_pValues = [posthoc_results['StudySite']['Control1'], posthoc_results['StudySite']['Control2'], posthoc_results['StudySite']['Control3']]
        max_pvalue_post_hoc = max(post_hoc_study_pValues)
            
        if sorted_medians.index[-1] == 'StudySite':

            if p_value_kruskal < 0.05 and max_pvalue_post_hoc < 0.05:
                print(f'{dam_name} is a flood prone site statistically based on flood intensity analysis using ranking and Kruskal-Wallis test')
                test_results['Test2:'] = 1
            else:
                print(f'{dam_name} might be a flood prone site but it is not statistically significant based on flood intensity analysis using ranking and Kruskal-Wallis test')
                test_results['Test2:'] = 2

        elif sorted_medians.index[0] == 'StudySite':
            
                if p_value_kruskal < 0.05 and max_pvalue_post_hoc < 0.05:
                    print(f'{dam_name} is a protected site statistically based on flood intensity analysis using ranking and Kruskal-Wallis test')
                    test_results['Test2:'] = 5
                else:
                    print(f'{dam_name} might be a protected site but it is not statistically significant based on flood intensity analysis using ranking and Kruskal-Wallis test')
                    test_results['Test2:'] = 4
        else:
            print(f'{dam_name} is neither a flood prone site nor a protected site based on flood intensity analysis using ranking and Kruskal-Wallis test')
            test_results['Test2:'] = 3
            

        #Final result
        # Interpret the combined score
        print(f"Statistically, the study site can be classified as '{interpret_combined_score(test_results)[1]}', with a combined decision score of {interpret_combined_score(test_results)[0]}.")    
        
        results_df = pd.DataFrame({'Study Site': dam_name, 'Test1': test_results['Test1:'], 'Test2': test_results['Test2:'], 'Combined Score': interpret_combined_score(test_results)[0], 'Status': interpret_combined_score(test_results)[1]}, index = [0])
        # concating to the output
        output_df = pd.concat([output_df, results_df], axis = 0)

        
    except Exception as e:
        print(f'Error in processing {dam_name} due to error: {e}')
        results_df = pd.DataFrame({'Study Site': dam_name, 'Test1': 9999, 'Test2': 9999, 'Combined Score': 9999, 'Status': 'Error'}, index = [0])
        output_df = pd.concat([output_df, results_df], axis = 0)
        error_list.append(dam_name)
        continue

output_df.to_csv(output_fp + '.csv', index = False)