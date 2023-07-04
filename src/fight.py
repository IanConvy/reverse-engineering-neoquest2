
# This module contains all classes and functions which involve
# the status of combatants during a fight.

class FightState():

    # This class holds the status of all combatants during a 
    # given fight turn, and provides methods for extracting 
    # relevant information.

    def __init__(self, fight_dict):

        # 'fight_dict' is the data structure returned by the 
        # auto-player driver's `get_fight_dict` method.

        self.players  = fight_dict["players"]
        self.rohane = self.players.get("Rohane")
        self.mipsy = self.players.get("Mipsy")
        self.talinia = self.players.get("Talinia")
        self.velm = self.players.get("Velm")

        self.enemies = fight_dict["enemies"]
        self.potions = fight_dict["potions"]
        self.abilities = fight_dict["abilities"]
        self.messages = fight_dict["messages"]
        self.time = fight_dict["elapsed_time"]
        self.ended = fight_dict["ended"]

    def is_player_turn(self):

        # This method returns "true" if is the player's turn.

        check = any([("now" in player_dict["time"]) for player_dict in self.players.values()])
        return check

    def get_whos_turn(self):

        # This method returns the name of the combatant whose move 
        # it is.

        for agent_dict in (self.players | self.enemies).values():
            if agent_dict["time"] == "now":
                turn = f"{agent_dict['name']}"
                break
        return turn

    def get_alive_enemies(self):

        # This method returns a list of ids for enemies who are still
        # alive.

        alive = []
        for (i, enemy_dict) in self.enemies.items():
            if int(enemy_dict["curr_health"]) > 0:
                alive.append(i)
        return alive
    
    def get_health(self, char_id):

        # This method returns the hitpoints of the combatant with the
        # specified id.

        (curr_health, max_health) = (None, None)
        for (dict_id, agent_dict) in (self.players | self.enemies).items():
            if dict_id == char_id:
                curr_health = int(agent_dict["curr_health"])
                max_health = int(agent_dict["max_health"])
                break
        return (curr_health, max_health)

    def ability_is_active(self, ability_type):

        # This method returns "true" if the specified ability is
        # available to use.

        active = False
        for ability_string in self.abilities:
            if ability_type in ability_string:
                active = True
                break
        return active
    
    def is_potion(self, potion_name):

        # This method return "true" if the specified potion
        # is available to use.

        in_inv = (potion_name in self.potions)
        return in_inv
