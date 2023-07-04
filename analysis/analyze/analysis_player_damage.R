library(tidyverse)
library(tidymodels)
library(binom)

source("load/load_fight_status.R")
source("load/load_status.R")
source("transform/get_fight_moves.R")
source("transform/get_buffs.R")

# Generate cleaned player damage data for analysis and plotting.

# -------------------------------------------------------------------------

# Get player attacks:

player_attacks <- local({
  
  # Get monster info:
  
  monsters <- 
    fight_status |>
    filter(type == "enemy") |>
    rename(enemy = name, enemy_health = max_health) |>
    distinct(enemy, enemy_health) |>
    mutate(enemy_level = enemy_health / 5 - 1)
  
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
  
  # Get only melee attacks made by an enemy:
  
  fight_moves_buffs |>
    filter(action == "melee", actor == "Rohane", speed > 0) |>
    inner_join(
      monsters |> select(!enemy_health), 
      join_by(target == enemy)
    ) |>
    mutate(level_diff = level - enemy_level)
  
})

# Create histograms of damage dealt to each enemy:

ggplot(filter(player_attacks, level_diff == 1, damage == 0, dmg_buff == 0),
       aes(x = amount, y = after_stat(prop))
) + geom_bar() +  scale_x_continuous(breaks = seq(0, 100, 1)) + 
  facet_wrap(~target, scales = "free")

# Get the average damage and upper/lower damage bounds:

player_attacks_summary <- 
  player_attacks |>
  filter(amount > 0) |>
  summarize(
    lower = min(amount),
    upper = max(amount),
    avg = mean(amount),
    count = n(),
    .by = c(target, level, enemy_level, level_diff, damage, dmg_buff)
  ) |>
  arrange(target, level)

# Fit a linear model to the damage bounds:

linear_reg() |>
  set_engine("lm") |> 
  fit(upper ~ level, 
      player_attacks_summary |> 
        filter(enemy_level < 9,  target != "miner ghost",
               level_diff == 4, dmg_buff == 0, damage == 3, !(enemy_level == 3 & lower == 4)) |>
        mutate(damage = factor(damage, levels = c(0, 3)))
  )

# Create plot of upper and lower damage bounds versus enemy level at a chosen level gap:

ggplot() + 
  geom_point(
    aes(x = enemy_level, y = value, shape = bound, color = damage, size = damage),
    player_attacks_summary |> filter(enemy_level < 9,  target != "miner ghost",
                                     level_diff == 4, dmg_buff == 0, !(enemy_level == 3 & lower == 4)) |>
      mutate(damage = factor(damage, levels = c(0, 3))) |>
      pivot_longer(cols = c(lower, upper), names_to = "bound", values_to = "value") |>
      arrange(desc(damage))) + 
  scale_y_continuous(breaks = seq(1, 30, 1)) + 
  scale_x_continuous(breaks = seq(1, 30, 1)) + 
  scale_size_manual(values = c(3, 5)) + 
  guides(shape = guide_legend(override.aes = list(size = 3))) + 
  labs(
    title = "Damage Bounds at Equal Level",
    x = "Enemy Level",
    y = "Damage Bound",
    color = "Weapon\nDamage",
    shape = "Bound",
    size = "Weapon\nDamage"
  )

# Get the frequency of player attacks by player and enemy level:

player_attack_freq <- 
  player_attacks |>
  group_by(level, enemy_level, level_diff, damage, dmg_buff, amount) |>
  summarize(count = n(), .groups = "drop_last") |>
  mutate(
    total = sum(count), 
    freq = count / total,
    conf = binom.wilson(count, total),
    conf_lower = conf[["lower"]],
    conf_upper = conf[["upper"]]
  ) |>
  select(level, enemy_level, level_diff, damage, dmg_buff, amount, count, total, freq, conf_lower, conf_upper)

# Create a plot of miss frequency versus enemy level when player/enemy levels are equal:

ggplot(player_attack_freq |> filter(enemy_level < 10, amount == 0, level_diff == 0, 
                                    dmg_buff == 0, damage == 3), 
       aes(x = enemy_level, y = freq)) + 
  geom_bar(stat = "identity")

# Get average player miss rate:

player_attack_freq |>
  filter(enemy_level < 10, amount == 0, level_diff == 0, dmg_buff == 0, damage == 3) |>
  ungroup() |>
  mutate(weighted = freq*count / sum(count)) |>
  summarize(total = sum(weighted))
