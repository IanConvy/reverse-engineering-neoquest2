library(tidyverse)
source("load/load_fight_ends.R")
source("load/load_fight_status.R")

# Extract the loot (gold, items, experience) awarded at the end of each fight.

loot <- local({
  
  # Get victories and initial status of each fight:
  
  victories <- 
    fight_end |>
    filter(str_detect(message, "You won"))
  
  first_turn <- 
    fight_status |>
    filter(turn_id == 0)
  
  # Focus only on encounters with one enemy:
  
  ids_multiple_enemies <- 
    first_turn |>
    filter(type == "enemy" & char_id > 5) |>
    distinct(game_id, move_id)
  
  victories_single <- 
    victories |>
    anti_join(
      ids_multiple_enemies, 
      join_by(game_id, move_id)
    )
  
  # Get enemy name:
  
  victories_with_enemy <- 
    victories_single |>
    inner_join(
      first_turn |>
        filter(type == "enemy") |>
        select(game_id, move_id, enemy = name),
      join_by(game_id, move_id)
    )
  
  # Separate different loot statements into distinct rows:
  
  statements <-
    victories_with_enemy |>
    separate_longer_delim(message, regex("[!.]")) |>
    filter(str_detect(
      message, 
      r"((gained \d+ experience)|found)"))
  
  # Get type and quantity of loot:
  
  loot_types <- 
    statements |>
    mutate(
      type = case_when(
        str_detect(message, "experience") ~ "exp",
        str_detect(message, "gold") ~ "gold",
        str_detect(message, "found") ~ str_remove( # Get item name (not plural)
          str_extract( 
            message, r"((?<=\d{1,2} ).*)"
          ),
          "s?$"
        )
      ),
      qty = as.double(str_extract(message, r"(\d+)"))
    ) |>
    select(!message)
})
