##This script download GlobPop dataset for years 1990-2020
# The dataset is available at https://zenodo.org/records/10088105

import requests
import geopandas as gpd
import pandas as pd
import rioxarray
import numpy as np
import os
from tqdm import tqdm

output_path = ''

download_url = 'https://zenodo.org/records/10088105/files/GlobPOP_Count_30arc_{}_I32.tiff'

for year in range(1990, 2021):
    url = download_url.format(year)
    print('Downloading {}'.format(year), url)
    response = requests.get(url)
    with open(f'{output_path}/GlobPop_{year}.tiff', 'wb') as f:
        f.write(response.content)
    print('Downloaded', url)