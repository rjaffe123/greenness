library(rgdal)
library(raster)
library(jsonlite)
library(httr)
library(dplyr)
library(stringr)
library(tidyr)

## the file takes the final file created in the inputTaskID.R file and makes it tidy data for processing. 

data <- read.csv("/Users/rachaeljaffe/NDVI/final_file_500m_2009.csv")
data <- data %>% select (-matrix..)
data <- data %>% select (-X)
data <- data %>% select (-'X353')
data <- data %>% rename(X353 = X353.1)

for (x in colnames(data)){
   if (grepl('X', x)){
     name = paste("IS_NA_", x, sep = "")
     data <- data %>% mutate(!!name := case_when(
        is.na(data[x]) == TRUE ~ "1",
        is.na(data[x]) == FALSE ~ "0"),)
   }
}

data <- data %>% select(PC, LONGITUD, LATITUDE, names(.)[-(1:3)][order(str_remove_all(names(.)[-(1:3)], '\\D+'))])

test_data <- data[1:5,]
data <- data %>% fill_(names(.), .direction="updown")

write.csv(data, "/Users/rachaeljaffe/NDVI/final_file_500m_2009_modified.csv")


