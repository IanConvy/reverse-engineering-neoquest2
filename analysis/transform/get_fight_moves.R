library(tidyverse)
source("load/load_fight_turns.R")
source("load/load_fight_status.R")

# Extract the action type, effect, target, and time of each combat move.

fight_moves <- local({

  # Define regex patterns and functions used for message parsing:
  
  melee_patterns = str_flatten(
    c(r"(\bhits?\b)", r"(\bclaws?\b)", r"(\bslash(es)?\b)", 
      r"(\bbites?\b)", r"(\bzaps?\b)", r"(\bcrush(es)?\b)",
      r"(\bbash(es)?\b)"),
    ")|("
  )
  
  melee_regex = str_c("((", melee_patterns, "))")
  
  get_target <- function(string) {
    str_remove(
          str_extract(
            string,
            str_c(
              "(?<=", melee_regex, r"( ).*(?=\b(,| for\b)))" 
            )
          ),
          "^an? "
        )
  }
  
  # Get time at start of turn:
  
  start_times <- 
    fight_turns |>
    inner_join(
      fight_turns |> mutate(turn_id = turn_id + 1),
      join_by(game_id, move_id, turn_id)
    ) |>
    select(
      game_id, move_id, turn_id, start_time = elapsed_time.y,
      end_time = elapsed_time.x, message = message.x
    )
  
  # Get type of action:
  
  action_type <- 
    start_times |>
    mutate(
      type = case_when(
        str_detect(message, r"(\bflee\b)") ~ "flee",
        str_detect(message, "critical") ~ "critical",
        str_detect(message, "stun") ~ "stun",
        str_detect(message, melee_regex) ~ "melee",
        str_detect(message, r"(\bcasts?\b)") ~ "spell",
        str_detect(message, "does nothing") ~ "wait"
      )
    )
  
  # Get actor at each turn:
  
  actors <- 
    fight_status |>
    filter(turn_time == "now") |>
    inner_join(
      action_type |> mutate(prev_turn_id = turn_id - 1),
      join_by(game_id, move_id, turn_id == prev_turn_id)
    ) |>
    select(game_id, move_id, turn_id = turn_id.y, 
           start_time, end_time, action = type.y, actor_id = char_id,
           actor = name, message) |>
    filter(!is.na(action))
  
  # Get target of each action:
  
  target <- 
    actors |>
    mutate(
      target = case_when(
        action == "flee" ~ "none",
        action == "wait" ~ "none",
        action == "spell" ~ "none",
        action == "critical" ~ get_target(
          str_remove(message, "critical hit")
        ),
        TRUE ~ get_target(message)
      )
    )
  
  # Get amount associated with the action:
  
  amount <- 
    target |>
    mutate(
      amount = if_else(
        action != "flee",
        coalesce(
          as.double(str_extract(message, r"(\d+)")),
          0
        ),
        if_else(
          str_detect(message, "blocked"),
          0,
          1
        )
      )
    ) |>
    select(!message)
  
  # Get time taken by action:
  
  time <- 
    amount |>
    inner_join(
      fight_status |>
        mutate(
          turn_time = if_else(turn_time == "now", "0", turn_time)
        ),
      join_by(game_id, move_id, turn_id, actor_id == char_id)
    ) |>
    mutate(
      speed = end_time - start_time + as.double(turn_time)
    ) |>
    select(game_id, move_id, turn_id, action, actor_id, 
           actor, target, amount, speed)
})
