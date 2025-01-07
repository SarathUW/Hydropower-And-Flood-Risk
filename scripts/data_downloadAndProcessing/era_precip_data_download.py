import cdsapi
import os
#Note: use the .onering conda env located at /water3/saraths/Research_Files/Study2/marysville/.onering

# User input for timeframe
year_start = '1981'
year_end = '2023'

# create year list betweeb year_start and year_end
years = list(map(str, range(int(year_start), int(year_end)+1)))


c = cdsapi.Client()

output_fp= '/water3/saraths/Research_Files/Study2/ERA_precip/data_raw'
error_list = []
counter = 1
print(f'Downloading ERA5 precipitation data for years {year_start} to {year_end}')
for year in years:

    output_fn = f'{output_fp}/ERA5_precip_{year}.nc'
    if not os.path.exists(output_fn):
        print(f'{counter}.Year: {year}')
        try:
            c.retrieve(
                'reanalysis-era5-land',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': 'total_precipitation',
                    'month': [
                        '01', '02', '03',
                        '04', '05', '06',
                        '07', '08', '09',
                        '10', '11', '12',
                    ],
                    'year':year,
                    'day': [
                        '01', '02', '03',
                        '04', '05', '06',
                        '07', '08', '09',
                        '10', '11', '12',
                        '13', '14', '15',
                        '16', '17', '18',
                        '19', '20', '21',
                        '22', '23', '24',
                        '25', '26', '27',
                        '28', '29', '30',
                        '31',
                    ],
                    'time': [
                        '00:00',
                    ],
                },
                output_fn)
        except Exception as e:
            print(f'Error downloading {year}. Details: {e}')
            error_list.append(year)
            counter += 1
        else:
            counter += 1
    else:
        print(f'{year} already downloaded. Skipping')

print(f'Downloaded {counter} files with {len(error_list)} errors. Error years: {error_list}')