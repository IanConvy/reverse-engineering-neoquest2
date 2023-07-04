library(tidyverse)
library(RSQLite)

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

# Load contents of inventory for turns after a fight (when the contents might have
# changed).

inventory <-
  conn |> tbl("inventory") |> collect() |>
  mutate(equipped = as.logical(equipped))

dbDisconnect(conn)
rm(conn)