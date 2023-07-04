import sqlite3
import threading

from . import fight, inventory, characters, explore, skills, logs

# This module contains the logic needed to run iterations of NeoQuest's game
# loop. A GameThread instance is created and run in 'main.py', which then executes
# calls to other helper functions that process the game step.

class GameState():

    # This class holds all relevant game information, and is updated after each
    # game loop iteration. Its structure is subdivided into a set of four smaller
    # state objects, each of which stores data from a different part of the game.
    # The '*_dict' arguments in '__init__' and the four update methods all
    # expect specific data structures returned by the auto-player driver after
    # calling its 'get_*_dict' or 'get_*_list' methods. 

    def __init__(self, game_id, move_id, explore_dict = None, characters_dict = None, inventory_list = None, skills_dict = None):
        self.game_id = game_id
        self.move_id = move_id
        if explore_dict is not None:
            self.update_explore(explore_dict)
        else:
            self.explore = None
        if characters_dict is not None:
            self.update_characters(characters_dict)
        else:
            self.characters = None
        if inventory_list is not None:
            self.update_inventory(inventory_list)
        else:
            self.inventory = None
        if skills_dict is not None:
            self.update_skills(skills_dict)
        self.live = True

    def update_explore(self, explore_dict):
        self.explore = explore.ExploreState(explore_dict)

    def update_characters(self, characters_dict):
        self.characters = characters.CharactersState(characters_dict)
        
    def update_inventory(self, inventory_list):
        self.inventory = inventory.InventoryState(inventory_list)

    def update_skills(self, skills_dict):
        self.skills = skills.SkillsState(skills_dict)

class GameThread(threading.Thread):

    # This class inherits from Python's threading object, and is used
    # to run the game loop in parallel with the input loop created by
    # 'main.py'. Unless manually stopped, the thread will run until 
    # the Schedule instance is exhausted. 

    def __init__(self, flag, driver, schedule, logging, callback = None):

        # An instance is initialized with a control flag to allow for manual
        # termination, a driver instance (only accepts a `Driver` from 'neo_driver.py' 
        # currently), a Schedule instance from config.py', a boolean that control whether
        # data should be logged, and an optional callback function.

        super().__init__()
        self.schedule = schedule
        self.flag = flag
        self.driver = driver
        self.callback = callback
        self.log = logging

    def run(self):

        # When run, the GameThread instance will create a connection to the SQLite
        # database, create and new GameState instance and update it using the current
        # game state (the game does not have to be restarted), log the initial state,
        # retrieve the first handler, and then start the game loop. Each loop iteration
        # is processed by the 'game_step' function, with the GameThread instance only
        # checking to see if a new handler needs to be assigned or if the game needs to
        # be reset. Once every handler has been assigned and released, the game loop
        # terminates.

        conn = (sqlite3.connect("data.db") if self.log else sqlite3.connect("test.db"))
        game_id = logs.get_next_game_id(conn)
        game_state = GameState(game_id, move_id = 0)
        state_update(self.driver, game_state, ["characters", "inventory", "skills", "explore"])
        if game_state.move_id == 0:
            logs.log_all(game_state, conn)
        (handler, state) = self.schedule.get_next_handler()
        while self.flag[0]: # Can be manually terminated by the input loop in 'main.py'
            if state == "released":
                break
            if self.callback:
                self.callback(game_state)
            game_state = game_step(self.driver, game_state, handler, conn)
            if not game_state.live:
                if state == "reset":
                    self.driver.reset_game()
                    game_id = logs.get_next_game_id(conn)
                    game_state = GameState(game_id, move_id = 0)
                    state_update(self.driver, game_state, ["characters", "inventory", "skills", "explore"])
                (handler, state) = self.schedule.get_next_handler()
                game_state.live = True
        conn.close()
        print("Released")

def game_step(driver, game_state, handler, conn):

    # This function runs a single step of NeoQuest II using the
    # specified handler. First, a move is made by the move handler,
    # which may trigger a fight. If so, control is passed to `fight_loop`
    # until the fight has concluded. After that, the state of the game 
    # is updated and any requested inventory or skill actions are performed.
    # Finally, the step is concluded by logging all relevant game data.

    fought = False
    moved = make_move(driver, handler, game_state)
    if not moved:
        game_state.live = False
        return game_state
    game_state.move_id += 1
    if driver.is_fighting():
        fight_loop(driver, handler, game_state.game_id, game_state.move_id, conn)
        fought = True
    state_update(driver, game_state, ["explore", "characters"])
    process_inventory(driver, handler, game_state, update = fought)
    process_skills(driver, handler, game_state, update = fought)

    logs.log_explore_info(game_state, conn)
    logs.log_status_info(game_state, conn)
    logs.log_item_info(game_state, conn)
    logs.log_skill_info(game_state, conn)
    driver._log_local_map(conn)
    return game_state

def make_move(driver, handler, game_state):

    # This function executes the next move or action from the
    # assigned move handler. The handler will continue to be
    # queried until the map position changes or a fight begins.

    old_coords = game_state.explore.coords
    while True:
        direction = handler.get_move_action(game_state)
        if direction == "release":
            return False
        if direction not in ["n", "s", "e", "w", "nw", "ne", "sw", "se"]:
            driver.action(direction)
        else:
            driver.move(direction)
        if driver.is_fighting() or driver.get_explore_dict()["coords"] != old_coords:
            break
    return True

def fight_loop(driver, handler, game_id, move_id, conn):

    # This function handles the combat loop during an encounter, with each 
    # iteration consisting of either a player or enemy move. During the
    # player's moves, actions are returned by the assigned fight handler
    # based on the current game state. After all enemies or party members
    # are defeated, the fight loop terminates.

    turn_id = 0
    driver.begin_fight()
    fight_dict = driver.get_fight_dict()
    fight_state = fight.FightState(fight_dict)
    logs.log_fight(fight_state, game_id, move_id, turn_id, conn)
    while not fight_state.ended:
        if fight_state.is_player_turn():
            make_fight_move(driver, handler, fight_state)
        else:
            driver.take_enemy_turn()
        fight_dict = driver.get_fight_dict()
        fight_state = fight.FightState(fight_dict)
        turn_id += 1
        logs.log_fight(fight_state, game_id, move_id, turn_id, conn)
    driver.end_fight()
    end_message = driver.get_fight_end_message()
    logs.log_fight_end(game_id, move_id, end_message, conn)
    driver.return_from_fight()

def make_fight_move(driver, handler, fight_state):

    # This function executes the next fight action from the
    # assigned fight handler.

    action = handler.get_fight_action(fight_state)
    while "trg" in action: # Targetting does not count as a full action
        target_id = action[-1]
        driver.choose_target(target_id)
        action = handler.get_fight_action(fight_state)
    if "wt" in action:
        time = action[-1]
        driver.wait(time)
    elif action == "attk":
        driver.melee_attack()
    elif action == "flee":
        driver.flee()
    elif "ability" in action:
        ability_type = action.split("_")[-1]
        driver.use_ability(ability_type)
    elif "potion" in action:
        potion_name = action.split("_")[-1]
        driver.use_fight_potion(potion_name)

def process_inventory(driver, handler, game_state, update = True):

    # This function executes any inventory actions returned by the
    # assigned inventory handler. An optional 'update' argument
    # can be passed to determine whether a state update should be
    # requested from the driver.

    if update:
        state_update(driver, game_state, ["inventory"])
    action_type = ""
    while action_type != "nothing":
        (action_type, action) = handler.get_inventory_action(game_state)
        if action_type == "heal":
            (potion_name, char_id) = action.split("_")
            driver.drink_inventory_potion(potion_name, char_id)
            state_update(driver, game_state, ["inventory", "characters"])
    
def process_skills(driver, handler, game_state, update = True):

    # This function executes any skill point actions returned by the
    # assigned skills handler. An optional 'update' argument can be
    # passed to determine whether a state update should be requested
    # from the driver.

    if update:
        state_update(driver, game_state, ["skills"])
    action = handler.get_skills_action(game_state)
    while action != "nothing":
        (char_name, skill, points) = action.split("_")
        driver.upgrade_skill(char_name, skill, points)
        state_update(driver, game_state, ["skills"])
        action = handler.get_skills_action(game_state)

def state_update(driver, game_state, info_sequence):

    # This function updates the passed GameState instance with 
    # the types of data requested in the 'info_sequence' string
    # list.

    for info_type in info_sequence:
        if info_type == "characters":
            characters_dict = driver.get_characters_dict()
            game_state.update_characters(characters_dict)
        if info_type == "inventory":
            inventory_list = driver.get_inventory_list()
            game_state.update_inventory(inventory_list)
        if info_type == "skills":
            skills_dict = driver.get_skills_dict()
            game_state.update_skills(skills_dict)
        if info_type == "explore":
            explore_dict = driver.get_explore_dict()
            game_state.update_explore(explore_dict)