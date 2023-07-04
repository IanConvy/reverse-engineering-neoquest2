
# This module contains inventory handler classes with different
# patterns of behavior.

class SimpleHeal():

    # This handler will consume healing potions (from weakest to strongest)
    # until all characters have less than 7 damage.

    def __init__(self):
        pass

    def perform(self, game_state):

        # This method is designed to be called repeatedly until it returns
        # a blank action string. 

        injured_ids = game_state.characters.get_injured_ids(dmg_thresh = 7)
        inventory = game_state.inventory
        (action_type, action) = ("nothing", "")
        if injured_ids:
            char_id = injured_ids[0]
            if inventory.get_item("Healing Vial"):
                (action_type, action) = ("heal", f"Healing Vial_{char_id}")
            elif inventory.get_item("Healing Flask"):
                (action_type, action) = ("heal", f"Healing Flask_{char_id}")
            elif inventory.get_item("Healing Potion"):
                (action_type, action) = ("heal", f"Healing Potion_{char_id}")
        return (action_type, action)

class DoNothing():

    # This handler will never use any inventory items.

    def __init__(self):
        pass

    def perform(self, game_state):
        (action_type, action) = ("nothing", "")
        return (action_type, action)