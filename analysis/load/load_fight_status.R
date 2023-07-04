library(tidyverse)
library(RSQLite)

# Loads the hitpoints and move times of combatants during each fight turn.

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

fight_status <-
  conn |> tbl("fight_status") |> collect() |>
  filter( # Remove fight with attack glitch
    game_id != 15 & move_id != 420
  ) |>
  mutate(
    char_id = if_else(type == "enemy", char_id + 4, char_id),
    name = str_remove(name, r"(^an? )"),
    turn_time = coalesce(
      if_else( # Remove " sec" from time string
        turn_time == "now",
        "now",
        str_extract(turn_time, r"(\d+\.\d+)")
      ), 
      "dead"
    ),
    # Earlier games had the move_id logged incorrectly
    move_id = if_else(game_id < 33, move_id + 1, move_id)
  )

dbDisconnect(conn)
rm(conn)