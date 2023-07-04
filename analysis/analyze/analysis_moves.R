library(tidyverse)
library(binom)

source("load/load_fight_status.R")
source("transform/get_moves.R")

# Generate cleaned move data for analysis and plotting.

# -------------------------------------------------------------------------

# Get all moves that were concentrated at single location: 

valid_moves <- 
  filter(moves, !(game_id >= 64 & game_id <= 78))

# Get the previous move for each move:

prev_move <- 
  valid_moves |>
  left_join(
    valid_moves |>
      select(game_id, move_id, encounter) |>
      mutate(next_move_id = move_id + 1),
    join_by(game_id, move_id == next_move_id),
    suffix = c("_1", "_0")
  ) |>
  mutate(encounter_0 = coalesce(encounter_0, FALSE)) |>
  select(!move_id_0)

# Get encounter rates and confidence intervals for moves that do not follow a 
# previous encounter (encounters are never back-to-back):

enc_freq <- 
  prev_move |>
  filter(area_1 != "the village of Trestin", !encounter_0) |>
  summarize(moves = n(), enc_rate = mean(encounter_1), .by = c(mode, area_1)) |>
  mutate(
    conf = binom.wilson(enc_rate * moves, moves),
    conf_lower = conf[["lower"]],
    conf_upper = conf[["upper"]]
  ) |>
  select(area = area_1, mode, moves, enc_rate, conf_lower, conf_upper) |>
  arrange(area)

# Get rates of double encounters:

double_freq <- local({
  
  # Get enemies at start of encounters:
  
  enemies <- 
    fight_status |>
    filter(turn_id == 0, type == "enemy")
  
  # Retrieve encounters with more than on enemy:
  
  enemies |>
  select(game_id, move_id, char_id) |>
  summarize(double = any(char_id > 5), .by = c(game_id, move_id)) |>
  inner_join(
    valid_moves |> select(game_id, move_id, area_0),
    join_by(game_id, move_id)
  ) |>
  group_by(area_0) |>
  summarize(num_enc = n(), double_freq = mean(double))
  
}) 
  
# Get rates of enemies per map area:

enemy_freq <- local({
  
  # Get enemies at start of encounters:
  
  enemies <- 
    fight_status |>
    filter(turn_id == 0, type == "enemy")
  
  # Count encounters by map area:
  
  enemies |>
  filter(!(name %in% c("the miner foreman", "Zombom"))) |>
  select(game_id, move_id, name) |>
  inner_join(
    valid_moves |> select(game_id, move_id, area = area_1),
    join_by(game_id, move_id)
  ) |>
  select(area, name) |>
  group_by(area, name) |>
  summarize(count = n(), .groups = "drop_last") |>
  mutate(freq = count / sum(count)) |>
  filter(area != "the village of Trestin")
  
})
