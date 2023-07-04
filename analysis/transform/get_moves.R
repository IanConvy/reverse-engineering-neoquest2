library(tidyverse)
source("load/load_explore.R")
source("load/load_fight_ends.R")

# Extract starting and ending locations for each move, and whether an encounter
# occurred.

moves <- local({
  
  # Get start and end positions for move
  
  positions <- 
    explore |>
    inner_join(
      explore |> mutate(move_id = move_id + 1),
      join_by(game_id, move_id),
      suffix = c("_1", "_0")
    ) |>
    select(
      game_id,
      move_id,
      mode = travel_mode_1,
      area_0,
      area_1,
      x_0 = x_pos_0,
      x_1 = x_pos_1,
      y_0 = y_pos_0,
      y_1 = y_pos_1
    )
  
  # Add indication of whether combat occurred
  
  encounters <- 
    positions |>
    left_join(
      fight_end,
      join_by(game_id, move_id) 
    ) |>
    mutate(encounter = if_else(
      is.na(message),
      FALSE,
      TRUE)
    ) |>
    select(!message)
})
