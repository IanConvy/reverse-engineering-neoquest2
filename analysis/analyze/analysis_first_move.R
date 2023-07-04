library(tidyverse)

source("load/load_fight_turns.R")
source("load/load_fight_status.R")

# Generate cleaned initial fight move data for analysis and plotting.

# -------------------------------------------------------------------------

# Get time of first action and which combatant performed it, as well as the time
# gap between the first and second moves:

time_first_act <- local({
  
  # Get initial turn order for each encounter:
  
  move_order <-
    fight_turns |>
    filter(turn_id == 0) |>
    select(game_id, move_id, first_time = elapsed_time) |>
    inner_join(
      fight_status |> 
        filter(turn_id == 0),
      join_by(game_id, move_id)
    ) |>
    mutate(
      turn_order = if_else(turn_time == "now", "one", "two")
    ) |>
    arrange(game_id, move_id, turn_time)
  
  # Get time between first and second move
  
  time_gap <- 
    move_order |>
    mutate(
      turn_time = as.double(
        if_else(turn_time == "now", "0", turn_time)
      ), 
      gap = first(turn_time) - last(turn_time),
      .by = c(game_id, move_id)
    ) |>
    slice_head(n = 1, by = c(game_id, move_id, turn_order)) |>
    select(game_id, move_id, first_time, gap, name, turn_order) |>
    pivot_wider(
      id_cols = c(game_id, move_id, first_time, gap),
      names_from = turn_order,
      values_from = name
    )
})

# Get probability that the player moves first
# for different enemies

player_first <- 
  time_first_act |>
  mutate(
    enemy = if_else(one != "Rohane", one, two)
  ) |>
  summarize(freq = mean(one == "Rohane"), .by = enemy)

# Get time to first move for player and enemy:

agent_time <- 
  time_first_act |>
  mutate(
    R_time = if_else(
      one == "Rohane",
      first_time,
      first_time + gap
    ),
    E_time = if_else(
      one != "Rohane",
      first_time,
      first_time + gap
    )
  )

# Create plots of first move times for player and all enemies:

ggplot(agent_time, aes(x = R_time)) + 
  geom_histogram(bins = 15) + 
  scale_x_continuous(breaks = seq(0, 4, 0.1))

ggplot(agent_time, aes(x = E_time)) + 
  geom_histogram(bins = 30) + 
  scale_x_continuous(breaks = seq(0, 4, 0.1))

# Create 2D plot of enemy vs player time to check for correlation:

ggplot(agent_time, mapping = aes(x = R_time, y = E_time)) + 
  geom_count() + 
  scale_x_continuous(breaks = seq(0, 3, 0.1)) + 
  scale_y_continuous(breaks = seq(0, 3, 0.1)) +
  geom_rug() + 
  labs(size = "Count")