library(tidyverse)
library(tidymodels)

source("load/load_status.R")
source("transform/get_loot.R")

# Generate cleaned loot data for analysis and plotting.

# -------------------------------------------------------------------------

# Get all loot data with other relevant information:

loot_info <- local({
  
  # Get enemy data:
  
  enemies <- 
    fight_status |>
    filter(type == "enemy") |>
    mutate(
      enemy = name, 
      enemy_level = max_health / 5 - 1) |>
    distinct(enemy, enemy_level) |>
    arrange(enemy_level)
  
  # Join loot table with enemy and player status data:
  
  loot |>
  inner_join(
    status |>
      select(!c(exp, max_health, curr_health)) |>
      mutate(move_id = move_id + 1),
    join_by(game_id, move_id == move_id)
  ) |>
  inner_join(
    enemies,
    join_by(enemy)
  ) |>
  mutate(level_diff = level - enemy_level)
})

# GOLD --------------------------------------------------------------------

# Get gold information from loot:

gold <- 
  filter(loot_info, type == "gold")

# Get the mean and standard deviation of gold loot by enemy level, excluding bosses:

gold_mean_sd <- 
  gold |> 
  filter(level_diff < 7, !(enemy %in% c("the miner foreman", "Zombom"))) |>
  summarize(
    loot_count = n(),
    mean_qty = mean(qty), 
    sd_qty = sd(qty),
    .by = c(enemy_level))

# Get Gaussian probability densities that have been fit to the gold histograms:

gauss_est <- 
  gold_mean_sd |>
  mutate(
    qty = list(0:40), 
    prob = list(dnorm(0:40, mean_qty, sd_qty)), 
    .by = c(enemy_level, mean_qty, sd_qty)
  ) |>
  select(enemy_level, qty, prob) |>
  unnest(c(qty, prob))

# Create a gold vs player level scatter plot for each enemy:

ggplot(
  gold,
  aes(x = level, y = qty)
) + geom_jitter(width = 0.2) + scale_x_continuous(breaks = seq(1, 60, 1)) + 
  facet_wrap(~ enemy, scales = "free_y")

# Create gold histograms with Gaussian fit excluding level differences > 7 and bosses :
  
ggplot(
  gold |> 
    filter(level_diff < 7, !(enemy %in% c("the miner foreman", "Zombom"))) |>
    group_by(enemy_level, qty) |>
    summarize(count = n(), .groups = "drop_last") |>
    mutate(freq = count / sum(count))
    , 
  aes(x = qty, y = freq)
  ) + 
  geom_bar(stat = "identity") +
  geom_line(aes(qty, prob), data = gauss_est) + 
  scale_x_continuous(breaks = seq(0, 100, 2)) + 
  facet_wrap(~ enemy_level, scales = "free")

# Create plot for mean gold by enemy level (exclude level diff > 7 and bosses):

mean_fit <- # fit to individual samples, not means 
  linear_reg() |>
  set_engine("lm") |>
  fit(qty ~ enemy_level, data = gold |> 
        filter(level_diff < 7, !(enemy %in% c("the miner foreman", "Zombom"))))

mean_fit_points <- 
  gold_mean_sd |>
  bind_cols(predict(mean_fit, gold_mean_sd))

ggplot(gold_mean_sd,
       aes(x = enemy_level, y = mean_qty)) + 
  geom_point() + 
  geom_line(aes(x = enemy_level, y = .pred), 
            mean_fit_points)

# Create plot for deviation of gold by enemy level (exclude level diff > 7 and bosses):

sd_fit <- # fit to standard deviation estimates
  linear_reg() |>
  set_engine("lm") |>
  fit(sd_qty ~ enemy_level, data = gold_mean_sd |> filter(enemy_level != 9))

sd_fit_points <- 
  gold_mean_sd |> filter(enemy_level != 9) |>
  bind_cols(predict(sd_fit, gold_mean_sd |> filter(enemy_level != 9)))

ggplot(gold_mean_sd,
       aes(x = enemy_level, y = sd_qty)) + 
  geom_point() + 
  geom_line(aes(x = enemy_level, y = .pred), sd_fit_points)

# ITEMS -------------------------------------------------------------------

# Get loot item frequencies:

freq <- local({

  # Get qty already in inventory to determine when item limit is reached:
  
  items <- 
    loot_info |>
    select(game_id, move_id, level, enemy, enemy_level, type, qty) |>
    left_join( # Get prior quantities of items in inventory
      inventory |> 
        filter(str_detect(type, "Potion")) |>
        select(game_id, inv_move_id = move_id, name, quant),
      join_by(game_id, closest(move_id > inv_move_id))
    ) |>
    mutate(
      prev_qty = coalesce(as.double(quant), 0)) |>
    group_by(game_id, move_id, enemy, type, qty) |>
    slice_max(prev_qty, n = 1, with_ties = FALSE) |>
    ungroup() |>
    select(!c(name, inv_move_id, quant))
  
  # Get number of encounters which are below item cap:
  
  num_encounters <- 
    items |>
    filter(prev_qty != 20) |>
    distinct(enemy_level, game_id, move_id) |>
    summarize(encounters = n(), .by = enemy_level)
  
  # Compute item frequencies for :
  
    items |>
    filter(prev_qty != 20, level - enemy_level < 7, !(enemy %in% c("the miner foreman", "Zombom"))) |>
    mutate( # Tag parts of loot which don't involve items
      type = if_else(
        type == "gold" | type == "exp", 
        "no item", 
        type
      )
    ) |>
    distinct(game_id, move_id, type, .keep_all = TRUE) |>
    group_by(game_id, move_id) |>
    mutate(has_item = any(type != "no item")) |>
    filter(type != "no item" | !has_item) |>
    group_by(enemy_level, type) |>
    summarize(occurrences = n(), .groups = "drop_last") |>
    inner_join(
      num_encounters,
      join_by(enemy_level)
    ) |>
    mutate(freq = occurrences / encounters) |>
    arrange(type, desc(freq))

})

# Create scatter plot of item probabilities vs enemy level:

ggplot(freq,
       aes(enemy_level, freq)) + 
  geom_point() + 
  scale_x_continuous(breaks = seq(1, 10)) + 
  facet_wrap(~type, scales = "free_y")

# EXPERIENCE --------------------------------------------------------------

# Get experience points:

exp <- 
  loot_info |>
  filter(type == "exp") |>
  select(enemy, level_diff, qty)

# Create scatter plots of experience vs level difference for all enemies:

ggplot(exp, aes(x = level_diff, y = qty)) + 
  geom_point() + facet_wrap(~enemy, scales = "free") + 
  scale_y_continuous(breaks = seq(0, 200, 20)) + 
  scale_x_continuous(breaks = seq(-10, 10))

# Fit linear models before and after the 100 point threshold, excluding bosses and
# the miner ghost (bugged?):

fit_pos_diff <- 
  linear_reg() |>
  set_engine("lm") |>
  fit(qty ~ level_diff, data = filter(exp,
    level_diff >= 0, !(enemy %in% c("miner ghost", "the miner foreman"))
  ))

fit_neg_diff <- 
  linear_reg() |>
  set_engine("lm") |>
  fit(qty ~ level_diff, data = filter(exp,
    level_diff <= 0, !(enemy %in% c("miner ghost", "the miner foreman", "plains lupe"))
    ))
