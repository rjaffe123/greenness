# greenness
Gathering data from https://lpdaacsvc.cr.usgs.gov/appeears/. Used their API to download the data. Using NDVI data and postal code longitude/latitude (Ontario, Canada - [PCCF](https://crdcn.org/datasets/pccf-postal-code-conversion-file)) to determine a NDVI value at each postal code. 
Used ARCGIS with python and geostatistical packages in R. 

appears.py --> used ArcGIS to download data
other R files --> used open sourced GIS software and other spatial stats packages
