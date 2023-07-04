library(tidyverse)
library(RSQLite)

# Loads the player's location and gold.

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

explore <- 
  conn |>
  tbl("explore") |>
  collect()

dbDisconnect(conn)
rm(conn)