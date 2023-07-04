library(tidyverse)
library(RSQLite)

conn <- 
  dbDriver("SQLite") |>
  dbConnect("data.db")

# Loads the messages and elapsed time during each fight turn.

fight_turns <- 
  conn |> tbl("fight_turns") |> collect() |>
  filter( # Remove fight with attack glitch
    game_id != 15 & move_id != 420
  ) |>
  separate_wider_regex( # Get fight time as a number
    elapsed_time,
    patterns = c(
      elapsed_time = r"(\d*\.\d*)",
      ".*"
    )
  ) |>
  mutate(
    elapsed_time = as.double(elapsed_time),
    # Remove unneeded "Message " from start of fight message
    message = str_sub(message, start = 10),
    # Earlier games had the move_id logged incorrectly
    move_id = if_else(game_id < 33, move_id + 1, move_id)
  )

dbDisconnect(conn)
rm(conn)