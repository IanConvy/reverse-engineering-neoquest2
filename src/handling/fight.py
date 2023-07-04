import random

# This module contains fight handler classes with different
# patterns of behavior.

class FightPrompt():

    # This handler is used for manual control of the auto-player
    # by the user.

    def __init__(self):
        pass

    def perform(self, fight_state):

        # When queried, the handler returns whatever action was
        # inputted by the player.

        valid = False
        while not valid:
            action = input("Action: ")
            if "trg" in action:
                if action[-1] in {"5", "6", "7", "8"}:
                    action = f"trig_{action[-1]}"
                    valid = True
            elif "wt" in action:
                if action[-1] in {"1", "3", "5"}:
                    action = f"wt_{action[-1]}"
                    valid = True
            elif action in {"attk", "flee", "stop"}:
                valid = True
            else:
                print("Invalid action.")
        return action

class SimpleMelee():

    # This handler will either perform melee attacks or attempt to flee
    # based on the specified flee rate between 0 and 1.

    def __init__(self, flee_rate = 0):

        # A flee rate of 0 will forbid fleeing, while a rate of 1
        # will forbid attacking.

        self.target_picked = False
        self.flee_rate = flee_rate

    def perform(self, fight_state):

        # 'fight_state' is the current FightState instance. Before 
        # attacking, the handler targets the leftmost enemy that has 
        # not yet been defeated.

        if not self.target_picked:
            self.target_picked = True
            target = fight_state.get_alive_enemies()[0]
            action = f"trg_{target}"
        else:
            self.target_picked = False
            sample = random.uniform(0, 1)
            if (self.flee_rate > 0) and (sample <= self.flee_rate):
                action = "flee"
            else:
                action = "attk"
        return action
    
class UseAbility():

    # This handler will attempt to use the specified ability,
    # or perform a melee attack if the ability is unavailable.

    def __init__(self, ability):
        self.target_picked = False
        self.ability = ability

    def perform(self, fight_state):

        # Before attacking, the handler targets the leftmost enemy 
        # that has not yet been defeated.

        if not self.target_picked:
            self.target_picked = True
            target = fight_state.get_alive_enemies()[0]
            action = f"trg_{target}"
        else:
            self.target_picked = False
            if fight_state.ability_is_active(self.ability):
                action = f"ability_{self.ability}"
            else:
                action = "attk"
        return action
    
class UseDamagePotions():

    # This handler will attempt to use the specified damage potion,
    # or perform a melee attack if the potion is unavailable.

    def __init__(self):
        self.target_picked = False

    def perform(self, fight_state):

        # Before attacking, the handler targets the leftmost enemy 
        # that has not yet been defeated.

        if not self.target_picked:
            self.target_picked = True
            target = fight_state.get_alive_enemies()[0]
            action = f"trg_{target}"
        else:
            self.target_picked = False
            if fight_state.is_potion("Flare Potion"):
                action = f"potion_Flare Potion"
            else:
                action = "attk"
        return action

class DoNothing():

    # This handler will simply wait 5 seconds every turn.

    def __init__(self):
        pass

    def perform(self, fight_state):
        return "wt_5"