library(tidyverse)
library(RSQLite)

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

# Loads number of points assigned to skills at each turn. 

skills <- 
  conn |> 
  tbl("skills") |> 
  collect()

dbDisconnect(conn)
rm(conn)