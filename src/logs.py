
# This module contains functions which interface with the SQLite
# database used to store game data. All functions must be passed
# an active SQLite connection to operate.

def clear_logs(game_id, conn):

    # This function will delete all data associated with the passed
    # game ID.

    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE game_id = ?;", (game_id,))
    cursor.execute("DELETE FROM skills WHERE game_id = ?;", (game_id,))
    cursor.execute("DELETE FROM status WHERE game_id = ?;", (game_id,))
    cursor.execute("DELETE FROM explore WHERE game_id = ?;", (game_id,))
    cursor.execute("DELETE FROM fight_status WHERE game_id = ?;", (game_id,))
    cursor.execute("DELETE FROM fight_turns WHERE game_id = ?;", (game_id,))
    cursor.execute("DELETE FROM fight_end WHERE game_id = ?;", (game_id,))
    conn.commit()
    cursor.close()

def log_all(game_state, conn):

    # This function logs all information from the passed GameState instance.

    log_explore_info(game_state, conn)
    log_status_info(game_state, conn)
    log_item_info(game_state, conn)
    log_skill_info(game_state, conn)

def log_explore_info(game_state, conn):

    # This functions logs all data related to map exploration from 
    # the passed GameState instance.

    (x_pos, y_pos) = game_state.explore.coords
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO explore (game_id, move_id, area, x_pos, y_pos, travel_mode, gold)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (game_state.game_id, game_state.move_id, game_state.explore.area, x_pos, y_pos, 
              game_state.explore.travel_mode, game_state.explore.gold)
    )
    cursor.close()
    conn.commit()

def log_status_info(game_state, conn):

    # This functions logs all data related to party status from 
    # the passed GameState instance. 

    cursor = conn.cursor()
    for (name, info_dict) in game_state.characters.get_iter():
        cursor.execute(
            """
            INSERT INTO status (game_id, move_id, name, level, exp, curr_health, max_health)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (game_state.game_id, game_state.move_id, name, info_dict["level"], 
                  info_dict["exp"], info_dict["curr_health"], info_dict["max_health"])
        )
    cursor.close()
    conn.commit()

def log_item_info(game_state, conn):

    # This functions logs all data related to inventory items from 
    # the passed GameState instance.

    cursor = conn.cursor()
    cursor.execute( # Delete out-of-date info
            """
            DELETE FROM inventory
            WHERE game_id = ? AND move_id = ?;
            """, (game_state.game_id, game_state.move_id)
        )
    for item_dict in game_state.inventory.get_all():
        buff_string = ",".join([" ".join(tupl) for tupl in item_dict["buffs"]])
        cursor.execute(
            """
            INSERT INTO inventory (game_id, move_id, type, name, buffs, quant, equipped)
            VALUEs (?, ?, ?, ?, ?, ?, ?)
            """, (game_state.game_id, game_state.move_id, item_dict["type"], item_dict["name"], 
                  buff_string, item_dict["quant"], item_dict["equipped"])
        )
    cursor.close()
    conn.commit()

def log_fight(fight_state, game_id, move_id, turn_id, conn):

    # This functions logs all data related to combat from 
    # the passed FightState instance.

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO fight_turns (game_id, move_id, turn_id, elapsed_time, message)
        VALUES (?, ?, ?, ?, ?);
        """, (game_id, move_id, turn_id, fight_state.time, fight_state.messages)
    )
    for (i, player_dict) in enumerate(fight_state.players.values(), 1):
        cursor.execute(
            """
            INSERT INTO fight_status (game_id, move_id, turn_id, type, char_id, name, curr_health,
                                        max_health, turn_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (game_id, move_id, turn_id, "player", i, player_dict["name"],
                  player_dict["curr_health"], player_dict["max_health"], player_dict["time"])
        )
    for (j, enemy_dict) in fight_state.enemies.items():
        cursor.execute(
            """
            INSERT INTO fight_status (game_id, move_id, turn_id, type, char_id, name, curr_health,
                                        max_health, turn_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (game_id, move_id, turn_id, "enemy", j, enemy_dict["name"],
                  enemy_dict["curr_health"], enemy_dict["max_health"], enemy_dict["time"])
        )
    cursor.close()
    conn.commit()

def log_fight_end(game_id, move_id, end_message, conn):

    # This functions logs the passed fight end message.

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO fight_end (game_id, move_id, message)
        VALUES (?, ?, ?);
        """, (game_id, move_id, end_message)
    )
    cursor.close()
    conn.commit()

def log_skill_info(game_state, conn):

    # This functions logs all data related to skill points from 
    # the passed GameState instance.

    cursor = conn.cursor()
    for (char_name, skills_dict) in game_state.skills.get_iter():
        for (skill, skill_dict) in skills_dict.items():
            cursor.execute(
                """
                INSERT INTO skills (game_id, move_id, char_name, skill, level_name, points, buff)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (game_state.game_id, game_state.move_id, char_name, skill, 
                      skill_dict["level_name"], skill_dict["points"], skill_dict["buff"])
            )
    cursor.close()
    conn.commit()

def get_next_game_id(conn):

    # This function retrieves the next available game ID, 
    # incrementing by 1 each time.

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT(game_id)
        FROM explore;
        """
    )
    game_ids = [int(tupl[0]) for tupl in cursor.fetchall()]
    next_game_id = max(game_ids) + 1
    return next_game_id