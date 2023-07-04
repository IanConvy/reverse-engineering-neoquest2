library(tidyverse)
library(RSQLite)

# Loads the end-of-fight messages.

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

fight_end <-
  conn |> tbl("fight_end") |> collect() |>
  filter( # Remove fight with attack glitch
    game_id != 15 & move_id != 420
  ) |>
  mutate( # Earlier games had the move_id logged incorrectly
    move_id = if_else(game_id < 33, move_id + 1, move_id)
  )

dbDisconnect(conn)
rm(conn)