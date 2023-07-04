import ast

from . import handling

# This module translates the auto-player configuration specified
# in `config.yml` into a sequence of handler objects that will be
# passed into the game loop via a 'Sequence' instance. Aside from 
# the class definition, their are a set of functions which contain
# mappings between the congfig names and the handler classes. 

class Schedule():

    # This class acts as a scheduler for the handling configurations
    # that will be given to the auto-player.

    def __init__(self, config_dict):

        # The class is initialized with the dictionary generated after
        # parsing `config.yml'. It then uses this data to create the desired
        # handler instances and reset instructions.

        self.config_dict = config_dict
        self.cycle = config_dict["cycle"]
        self.handlers = [self._create_handler(config) for config in self.config_dict["segments"]]
        self.resets = [config["reset"] for config in self.config_dict["segments"]]
        self.handler_index = 0

    def get_next_handler(self):

        # This method acts as the sole interface between the auto-player 
        # and the Schedule instance. When called, it returns the next handler
        # in the sequence and an associated state string that tells the auto-player
        # if it needs to restart or terminate. If 'self.cycle' is true, the 
        # handlers are re-created and the sequence is started again after the sequence
        # is complete. Otherwise, the game loop is terminated after every handler has 
        # released.

        if self.handler_index >= len(self.handlers): 
            if self.cycle:
                self.handler_index = 0
                self.handlers = [self.create_handler(config) for config in self.config_dict["segments"]]
                (handler, state) = self.get_next_handler()
            else:
                handler = None
                state = "released"
        else:
            handler = self.handlers[self.handler_index]
            state = "alive" if not self.resets[self.handler_index] else "reset"
            self.handler_index += 1
        return (handler, state)

    def _create_handler(self, config):

        # This internal method retrieves the four sub-handlers by handing
        # their individual configurations off to a set of helper functions.

        move_handler = get_move_handler(config["move"])
        fight_handler = get_fight_handler(config["fight"])
        inventory_handler = get_inventory_handler(config["inventory"])
        skills_handler = get_skills_handler(config["skills"])
        handler = handling.Handler(move_handler, fight_handler, inventory_handler, skills_handler)
        return handler

def get_move_handler(config):

    # This function takes the specified move handler configuration
    # and returns a matching handler instance. The set of supported
    # move handlers are:
    #   - "random": Indefinitely moves along directions chosen uniformly 
    #           at random. Will avoid tiles given in the 'avoid' key.
    #   - "leave White River": Moves along a path from the inn at
    #           White River to the northern exit, then releases.
    #   - "foreman": Moves along a path from Rohane's mother in Trestin
    #           to the miner foreman boss, then releases after victory.
    #   - "Zombom": Moves along a path from Rohane's mother in Trestin
    #           to Zombom, then releases after victory.
    #   - "manual": Prompts the user for a movement direction.

    name = config["name"]
    if name == "random":
        avoid_coords = [get_location(location) for location in config["avoid"]]
        handler = handling.move.RandomWalk(avoid_coords)
    elif name == "leave White River":
        handler = handling.move.PathFollow("paths/whiteriver_out")
    elif name == "foreman":
        handler = handling.move.PathFollow("paths/foreman")
    elif name == "Zombom":
        handler = handling.move.PathFollow("paths/zombom")
    elif name == "manual":
        handler = handling.move.ExplorePrompt()
    else:
        raise ValueError(f'Move handler "{name}" not found.')
    return handler

def get_fight_handler(config):

    # This function takes the specified fight handler configuration
    # and returns a matching handler instance. The set of supported
    # fight handlers are:
    #   - "simple melee": Performs melee attacks, or attempts 
    #           to flee with probability from the 'flee' key-value pair.
    #   - "manual": Prompts the user for a fight action.

    name = config["name"]
    if name == "simple melee":
        flee = config["flee"]
        handler = handling.fight.SimpleMelee(flee)
    elif name == "manual":
        handler = handling.fight.FightPrompt()
    else:
        raise ValueError(f'Fight handler "{name}" not found.')
    return handler

def get_inventory_handler(config):

    # This function takes the specified inventory handler configuration
    # and returns a matching handler instance. The set of supported
    # inventory handlers are:
    #   - "simple heal": Will use a healing potion after a fight if
    #           more than 7 hitpoints have been lost.

    name = config["name"]
    if name == "simple heal":
        handler = handling.inventory.SimpleHeal()
    else:
        raise ValueError(f'Inventory handler "{name}" not found.')
    return handler

def get_skills_handler(config):

    # This function takes the specified inventory handler configuration
    # and returns a matching handler instance. The skills config is a 
    # list of key-value pairs {"name": x, "points": y}. The auto-player
    # will assign "y" points into skill "x" before moving onto the next
    # key-value set in the list.

    schedule = {}
    for (char_name, skill_list) in config.items():
        schedule[char_name] = [(s_dict["skill"], s_dict["points"]) for s_dict in skill_list]
    handler = handling.skills.SkillSchedule(schedule)
    return handler

def get_location(name_or_coords):

    # This helper function parses location strings, which can either be 
    # place names or arbitrary map tiles.

    coords = handling.move.locations.get(name_or_coords)
    if coords is None:
        coords = ast.literal_eval(name_or_coords)
    return coords