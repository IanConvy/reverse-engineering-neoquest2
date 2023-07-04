library(tidyverse)

source("load/load_status.R")
source("transform/get_fight_moves.R")
source("transform/get_buffs.R")

# Generate cleaned enemy damage data for analysis and plotting.

# -------------------------------------------------------------------------

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

# Get enemy attack speeds:

enemy_attacks_speed <- 
  fight_moves_buffs |>
  filter(action == "melee", !(actor %in% c("Rohane")), speed > 0)

# Create histogram of enemy attack speeds:

ggplot(
  filter(enemy_attacks_speed, speed_buff == 0), aes(x = speed)) + 
  geom_histogram() +
  scale_x_continuous(breaks = seq(0, 7, 0.1)) + 
  facet_wrap(~level, scales = "free_y")

# Get player attack speeds:

player_attacks_speed <- 
  fight_moves_buffs |>
  filter(action == "melee", actor == "Rohane", speed > 0)

# Create speed histograms as a function of haste skill:

ggplot(
  player_attacks_speed |>
    mutate(count = n(), .by = c(speed_buff, speed)) |>
    filter(count > 2),
  aes(x = speed)
) + geom_histogram() +  scale_x_continuous(breaks = seq(0, 10, 0.1)) + 
  facet_wrap(~speed_buff, scales = "free")

# Get upper and lower bounds of speed as a function of haste skill:

bounds <- 
  player_attacks_speed |>
  mutate(avg = mean(speed), .by = speed_buff) |>
  summarize(count = n(), .by = c(speed_buff, speed, avg)) |>
  filter(count > 2) |>
  summarize(low = min(speed), high = max(speed), .by = c(speed_buff, avg))

# Create plot of upper and lower bounds as a function of haste level:

ggplot(bounds |> pivot_longer(cols = c(low, high), names_to = "type", values_to = "value"),
       aes(x = speed_buff, y = value, color = type, shape = type)) + 
  geom_point(size = 3) +
  scale_x_continuous(breaks = 0:12) + scale_y_continuous(breaks = seq(2, 6, 0.2)) + 
  labs(
    title = "Recovery Time Bounds",
    x = "Haste Level",
    y = "Recovery Time")
