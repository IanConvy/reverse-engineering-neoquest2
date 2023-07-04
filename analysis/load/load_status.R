library(tidyverse)
library(RSQLite)

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

# Loads the level, experience points, and health of all party members at each turn.

status <-
  conn |>
  tbl("status") |>
  collect()

dbDisconnect(conn)
rm(conn)