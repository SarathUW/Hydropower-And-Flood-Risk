#Importing microsoft planetary computer packages for data download
import pystac_client
import planetary_computer
import odc.stac
from pystac.extensions.eo import EOExtension as eo
from shapely.geometry import box, Polygon

def data_download(time_of_interest,satellite,satellite_queryParams,key,area_of_interest=None,bbox=None, cloud_cover = 20, enclose_roi = False):
    #Setting private key for 
    planetary_computer.settings.set_subscription_key(key)
    
    #Opening link to Microsoft PC catalog using stac api
    try:
        catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace)
        print(f'\nConnected to Microsoft Planetary Computer via STAC for downloading {satellite} imagery')
        print(f'Timeframe: {time_of_interest}')
    except:
        print('Failed to connect to Microsoft Planetary Computer')
        return 0
    
    #Searching images for the satellite and query params
    if satellite == 'Landsat 8':
        search = catalog.search(
        collections=[satellite_queryParams[satellite]['collection']], 
        intersects=area_of_interest, 
        datetime=time_of_interest,    
        query={
                "eo:cloud_cover": {"lt": cloud_cover},
                "platform": {"eq": satellite_queryParams[satellite]['platform']},
                # "landsat:wrs_row": {"eq": satellite_queryParams[satellite]['row'] },
                # "landsat:wrs_path": {"eq": satellite_queryParams[satellite]['path']}
              })
    
    if satellite == 'landsat':
        search = catalog.search(
        collections=[satellite_queryParams], 
        intersects=area_of_interest, 
        datetime=time_of_interest,    
        query={
                "eo:cloud_cover": {"lt": cloud_cover},
              })
        
    if satellite == 'Sentinel 1':
        search = catalog.search(
        collections=[satellite_queryParams[satellite]['collection']], 
        intersects=area_of_interest, 
        datetime=time_of_interest,    
        )
        
    if satellite == 'Sentinel 2':
        search = catalog.search(
        collections=[satellite_queryParams['Sentinel 2']['collection']], 
        intersects = area_of_interest,
        datetime=time_of_interest, 
        query={"eo:cloud_cover": {"lt": cloud_cover}
              })
        
    items = search.item_collection()
    print(f"Found {len(items)} items for {satellite}")
    
    if enclose_roi == True:            
        items = []
        for item in search.items():
            polygons = []
            for coord_list in item.geometry["coordinates"]:
                polygons.append(Polygon(coord_list))
            if any([area_of_interest.within(p) for p in polygons]):
                items.append(item)

        # Print number of matching images
        print(f"Found {len(items)} items that completely enclose the roi")          
        return items
    
    else:
        return items
            
            
        