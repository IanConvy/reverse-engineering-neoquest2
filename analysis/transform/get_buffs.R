library(tidyverse)
source("load/load_inventory.R")
source("load/load_skills.R")

# Extract the buffs that Rohane receives from equipment and skills.

buffs <- local({

  # Prepare join table from game/move ids:
  
  ids <-
    inventory |>
    distinct(game_id, move_id) |>
    cross_join(
      data.frame(type = c("damage", "armor", "dmg_buff", "speed_buff"))
    )
  
  # Get buff values from equipment and skills
  
  equipment <- 
    inventory |>
    filter(equipped) |>
    rename(item = type) |>
    mutate(
      type = if_else(
        str_detect(item, "dmg"),
        "damage",
        "armor"
      ),
      value = as.double(str_extract(
        item,
        r"(\d+)"
      ))
    ) |>
    select(game_id, move_id, type, value)
  
  skill_values <- 
    skills |>
    mutate(
      type = case_match(
        skill,
        "Damage Increase" ~ "dmg_buff",
        "Innate Melee Haste" ~ "speed_buff"
      ) 
    ) |>
    filter(!is.na(type)) |>
    mutate(
      value = pmax(pmin(points + buff, 15), 0)
    ) |>
    select(game_id, move_id, type, value)
  
  # Combine everything together:
  
  buffs <- 
    ids |>
    left_join(
      union(equipment, skill_values),
      join_by(game_id, move_id, type)
    ) |>
    mutate(
      value = coalesce(value, 0)
    ) |>
    pivot_wider(
      id_cols = c(game_id, move_id),
      names_from = type,
      values_from = value,
      values_fill = 0
    ) |> 
    mutate( # Fix error in data on game 43
      damage = if_else(
        game_id == 43, 3, damage
      )
    )
})
