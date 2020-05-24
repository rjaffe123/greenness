# Import packages
import requests as r
import getpass, pprint, time, cgi
import json
import geopandas as gpd
import os, shutil, glob
import pandas as pd
from shapely.geometry import Polygon
import arcpy

aprx = arcpy.mp.ArcGISProject(r"C:\Users\Rachael Jaffe\Documents\ArcGIS\Projects\MyProject1\MyProject1.aprx")
print("project")

# Set input directory, change working directory
inDir = r"C:\Users\Rachael Jaffe\Documents\untitled"        # IMPORTANT: Update to reflect directory on your OS
os.chdir(inDir)                                      # Change to working directory
api = r'https://lpdaacsvc.cr.usgs.gov/appeears/api/'  # Set the AρρEEARS API to a variable

user = 'username'      # Input NASA Earthdata Login Username
password = 'password'

token_response = r.post('{}login'.format(api), auth=(user, password)).json() # Insert API URL, call login service, provide credentials & return json
                                                          # Remove user and password information
print(token_response)

product_response = r.get('{}product'.format(api)).json()                         # request all products in the product service
print('AρρEEARS currently supports {} products.'.format(len(product_response)))  # Print no. products available in AppEEARS

products = {p['ProductAndVersion']: p for p in product_response}
products['MOD13Q1.006']
prods = ['MOD13Q1.006']

lst_response = r.get('{}product/{}'.format(api, prods[0])).json()  # Request layers for the 2nd product (index 1) in the list: MOD11A2.006
list(lst_response.keys())

lst_response['_250m_16_days_NDVI']

layers =[(prods[0], '_250m_16_days_NDVI')]
lai_response = r.get('{}product/{}'.format(api, prods[0])).json()  # Request layers for the 1st product (index 0) in the list: MCD15A3H.006
list(lai_response.keys())
layers.append((prods[0],'_250m_16_days_NDVI'))# Print the LAI layer names

prodLayer = []
for l in layers:
    prodLayer.append({
            "layer": l[1],
            "product": l[0]
          })
#prodLayer

token = token_response['token']                      # Save login token to a variable
head = {'Authorization': 'Bearer {}'.format(token)} # Create a header to store token information, needed to submit a request

poly2 = Polygon([[-98.9057477, 57.5629947],
                 [-98.5542748, 40.9135116],
                 [-71.8423382, 40.8802938],
                 [-72.1938110, 56.7045049]])
poly_gdf = gpd.GeoDataFrame([1], geometry=[poly2])
poly_gdf1 = poly_gdf.to_json()
poly_gdf2 = json.loads(poly_gdf1)

projections = r.get('{}spatial/proj'.format(api)).json()
projs = {}                                  # Create an empty dictionary
for p in projections: projs[p['Name']] = p  # Fill dictionary with `Name` as keys
list(projs.keys())
projs['geographic']

task_name = "january_2014"
task_type =['area']
proj = projs['geographic']['Name']
outFormat = ['geotiff']
startDate = '01-01-2014'
endDate = '01-31-2014'
recurring = False

task = {
    'task_type': task_type[0],
    'task_name': task_name,
    'params': {
         'dates': [
         {
             'startDate': startDate,
             'endDate': endDate
         }],
         'layers': prodLayer,
         'output': {
                 'format': {
                         'type': outFormat[0]},
                         'projection': proj},
         'geo': poly_gdf2,
    }
}
print(task)
print("starting response")
task_response = r.post('{}task'.format(api), json=task, headers=head).json()  # Post json to the API task service, return response as json
task_response # Print task response
task_id = task_response['task_id']

status_response = r.get('{}status/{}'.format(api, task_id), headers=head).json()
status_response
starttime = time.time()
while r.get('{}task/{}'.format(api, task_id), headers=head).json()['status'] != 'done':
    print(r.get('{}task/{}'.format(api, task_id), headers=head).json()['status'])
    time.sleep(20.0 - ((time.time() - starttime) % 20.0))
print(r.get('{}task/{}'.format(api, task_id), headers=head).json()['status'])

if r.get('{}task/{}'.format(api, task_id), headers=head).json()['status'] == 'done':
    destDir = os.path.join(inDir, task_name)  # Set up output directory using input directory and task name
    if not os.path.exists(destDir):
        os.makedirs(destDir)
    bundle = r.get('{}bundle/{}'.format(api,task_id)).json()  # Call API and return bundle contents for the task_id as json
    tiff_files = {}  # Create empty dictionary
    for f in bundle['files']:
        tiff_files[f['file_id']] = f['file_name']  # Fill dictionary with file_id as keys and file_name as values

    #create a map:
    m = aprx.listMaps("Map")[0]

    rootdir = r"C:\Users\Rachael Jaffe\Documents\Postal codes linked to DA\csv_files"
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            #delete all previous map layers:
            layers = m.listLayers()
            for lyr in layers:
                m.removeLayer(lyr)

            # add ontario shp file as a layer
            ontario_path = r"C:\Users\Rachael Jaffe\Documents\untitled\ontario.shp"
            m.addDataFromPath(ontario_path)

            filepath_csv = os.path.join(subdir, file)
            year_csv = file[:4]
            overall_file = pd.read_csv(filepath_csv)
            xy_postal = arcpy.management.XYTableToPoint(filepath_csv,
                                                      inDir+r'\xy_postal',
                                                       "LONGITUD", "LATITUDE")
            m.addDataFromPath(xy_postal)
            for f in tiff_files:
                if "NDVI" in tiff_files[f]:
                    dl = r.get('{}bundle/{}/{}'.format(api, task_id, f), stream=True)  # Get a stream to the bundle file
                    filename = os.path.basename(cgi.parse_header(dl.headers['Content-Disposition'])[1]['filename'])  # Parse the name from Content-Disposition header
                    year_tiff = filename.split("_")[6][3:7]
                    day = filename.split("_")[6][7:]
                    if year_tiff == year_csv:
                        filepath = os.path.join(destDir, filename)  # Create output file path
                        print("opening: " + filename)
                        with open(filepath, 'wb') as f:  # Write file to dest dir
                            for data in dl.iter_content(chunk_size=8192):
                                f.write(data)
                        f.close()
                        m.addDataFromPath(filepath)
                        extract_by_mask = arcpy.sa.ExtractByMask(filepath, ontario_path)
                        # Exract values to points
                        extract_values = arcpy.sa.ExtractValuesToPoints(xy_postal, extract_by_mask,
                                                                        inDir+r'\extract_values',
                                                                        interpolate_values=True)
                        final_file = arcpy.conversion.TableToExcel(extract_values,
                                                                   inDir+r"\output" + year_csv + "_" + day + ".xlsx")

                        final_file = pd.read_excel(final_file[:][0])
                        overall_file[day] = final_file["RASTERVALU"]
                        overall_file.to_csv(inDir+r"\FINAL_CSV_" + year_csv + ".csv")


                        #delete all tiff files in the temporary folder:
                        for file_tiff in os.listdir(destDir):
                            path = os.path.join(destDir, file_tiff)
                            try:
                                if os.path.isfile(path) or os.path.islink(path):
                                    os.unlink(path)
                                elif os.path.isdir(path):
                                    shutil.rmtree(path)
                            except Exception as e:
                                print('Failed to delete %s. Reason: %s' % (path, e))

                        #delete extract_by_mask files and extract_values files
                        for filename in glob.glob(inDir +r'\extract_values*'):
                            os.remove(filename)







