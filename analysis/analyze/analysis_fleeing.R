library(tidyverse)
library(binom)

source("load/load_fight_status.R")
source("load/load_status.R")
source("transform/get_fight_moves.R")
source("transform/get_buffs.R")

# Generate cleaned fleeing data for analysis and plotting.

# ------------------------------------------------------------------------

# Get fleeing attempts by number of attempts per encounter

flee <- local({
  
  # Get fight moves along with character buffs from equipment and skills:
  
  fight_moves_buffs <- 
    fight_moves |>
    inner_join(
      status |>
        mutate(move_id = move_id + 1) |>
        select(game_id, move_id, level),
      join_by(game_id, move_id)
    ) |>
    left_join(
      buffs |>
        mutate(move_id = move_id + 1),
      join_by(game_id, closest(move_id >= move_id))
    ) |>
    mutate(
      across(
        c("damage", "armor", "dmg_buff", "speed_buff"),
        ~coalesce(., 0)
      )
    ) |>
    rename(move_id = move_id.x) |>
    select(!move_id.y)
  
  # Get fleeing data and associated enemies:
  
  fight_moves_buffs |>
    filter(action == "flee") |>
    mutate(attempt = row_number(), .by = c(game_id, move_id)) |>
    inner_join(
      fight_status |> 
        filter(turn_id == 0, char_id <= 5, type == "enemy") |>
        select(game_id, move_id, enemy = name),
      join_by(game_id, move_id)
    )
  
})

# Create plot of time taken after an unsuccessful flee:

ggplot(filter(flee, speed > 0), aes(x = speed)) + geom_histogram() +
  facet_wrap(~enemy)

# Create plot of number of flee attempts before success or death:

ggplot(slice_max(flee, attempt, by = c(game_id, move_id)), aes(x = attempt)) + 
  geom_histogram()

# Get flee success probability by attempt:

attempt_prob <- 
  flee |>
  summarize(flee_count = n(), prob = mean(amount), .by = c(attempt)) |>
  mutate(
    conf = binom.wilson(prob * flee_count, flee_count),
    conf_lower = conf[["lower"]],
    conf_upper = conf[["upper"]]
  ) |>
  select(attempt, flee_count, prob, conf_lower, conf_upper)

# Get flee success probability by enemy:  

enemy_prob <- 
  flee |>
  summarize(flee_count = n(), prob = mean(amount), .by = c(enemy)) |>
  mutate(
    conf = binom.wilson(prob * flee_count, flee_count),
    conf_lower = conf[["lower"]],
    conf_upper = conf[["upper"]]
  ) |>
  select(enemy, flee_count, prob, conf_lower, conf_upper)

# Get flee success by level:

level_prob <- 
  flee |>
  summarize(flee_count = n(), prob = mean(amount), .by = c(level)) |>
  mutate(
    conf = binom.wilson(prob * flee_count, flee_count),
    conf_lower = conf[["lower"]],
    conf_upper = conf[["upper"]]
  ) |>
  select(level, flee_count, prob, conf_lower, conf_upper)

# Get average success:

attempt_prob |> 
  mutate(weighted = flee_count * prob / sum(flee_count)) |>
  summarize(est = sum(weighted))