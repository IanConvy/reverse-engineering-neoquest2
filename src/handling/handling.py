
# This module holds the Handler class, which acts as a thin wrapper to
# the four subhandlers.

class Handler():

    # This class simply forwards any action requests to the appropriate subhandler.

    def __init__(self, move_handler, fight_handler, inventory_handler, skills_handler):
        self.move_handler = move_handler
        self.fight_handler = fight_handler
        self.inventory_handler = inventory_handler
        self.skills_handler = skills_handler

    def get_move_action(self, game_state):
        action = self.move_handler.perform(game_state)
        return action

    def get_inventory_action(self, game_state):
        action = self.inventory_handler.perform(game_state)
        return action
    
    def get_skills_action(self, game_state):
        action = self.skills_handler.perform(game_state)
        return action
        
    def get_fight_action(self, fight_state):
        action = self.fight_handler.perform(fight_state)
        return action
