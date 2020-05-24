library(rgdal)
library(raster)
library(jsonlite)
library(httr)
library(dplyr)


## this code gets the taskID from the appeears webtool after you have 
## submitted their data through their online platform.


user = 'username'      # Input NASA Earthdata Login Username
password = 'password'
secret <- base64_enc(paste(user, password, sep = ":"))
api = 'https://lpdaacsvc.cr.usgs.gov/appeears/api/'
print('about to submit login')
response <- POST("https://lpdaacsvc.cr.usgs.gov/appeears/api/login", 
                 add_headers("Authorization" = paste("Basic", gsub("\n", "", secret)),
                             "Content-Type" = "application/x-www-form-urlencoded;charset=UTF-8"), 
                 body = "grant_type=client_credentials")
print(response)
token_response <- prettify(toJSON(content(response), auto_unbox = TRUE))
token <- paste("Bearer", fromJSON(token_response)$token)
print(token)

master_dataframe = data.frame(matrix())
postal_code <- read.csv("/home/rjaffe/2009.csv")
master_dataframe <- cbind(master_dataframe, postal_code)
coordinates(postal_code) = ~ LONGITUD + LATITUDE
dest_dir <- "/home/rjaffe/"
task_id <- "04b2bce4-55b8-47c8-a1cf-831577da21f2"
status = "done"
if (status == "done") {
  print('starting')
  response <-GET(paste("https://lpdaacsvc.cr.usgs.gov/appeears/api/bundle/", task_id, sep = ""), 
                 add_headers(Authorization = token))
  print("next")
  bundle_response <- prettify(toJSON(content(response), auto_unbox = TRUE))
  bundle <- fromJSON(bundle_response)$files
  for (file_id in bundle$file_id) {
    filename <- bundle[bundle$file_id == file_id, ]$file_name
    filepath <- paste(dest_dir, filename, sep = '')
    suppressWarnings(dir.create(dirname(filepath)))
    if (grepl("NDVI", filename) == TRUE) {
      response <- GET(paste("https://lpdaacsvc.cr.usgs.gov/appeears/api/bundle/", task_id,'/', file_id, sep = ""),
                      write_disk(filepath, overwrite = TRUE), progress(), add_headers(Authorization = token))
      split1 = strsplit(filename, "/")
      split2 = split1[[1]][2]
      split2 = strsplit(split2, "_")
      year_tiff <- substring(split2[[1]][7], 4, 7)
      day_tiff <- substring(split2[[1]][7], 8)
      print(day_tiff)
      print(paste("Using this file: ", filepath))
      raster_tiff <- raster(filepath)
      rasStack = stack(raster_tiff)
      rasValue = extract(rasStack, postal_code)
      combinePointValue = cbind(postal_code, rasValue)
      write.table(combinePointValue,
                  file = paste(dest_dir, year_tiff, "_", day_tiff, '.csv', sep = ""), append = FALSE, sep = ',' , 
                  row.names = FALSE, col.names = TRUE)
      print("wrote out csv file")
      filename_end_csv = paste(dest_dir, year_tiff, "_", day_tiff, '.csv', sep = "")
      current_data <- read.csv(filename_end_csv)
      vector_of_interest <- current_data[,2]
      new <- data.frame(as.matrix(vector_of_interest))
      colnames(new)<- day_tiff
      master_dataframe <- cbind(master_dataframe, new)
    }
  }
}
print("it finished, writing final file")
final_dest = paste(dest_dir, "final_file_500m_2009.csv", sep ="")
write.csv(master_dataframe, final_dest)
print("it actually got all the way through")