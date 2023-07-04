
# This module contains all classes and functions which involve
# the statuses of party members.

class CharactersState():

    # This class holds the state of the party members, stored 
    # internally as a dictionary. 

    def __init__(self, characters_dict):

        # `characters_dict` is the data structure returned by the 
        # auto-player driver's `get_characters_dict` method.

        self.characters_dict = characters_dict

    def __getitem__(self, char_name):
        char_dict = self.characters_dict[char_name]
        return char_dict
    
    def get_iter(self):
        itr = self.characters_dict.items()
        return itr
    
    def get_injured_ids(self, dmg_thresh = 1):

        # This method returns the ids of party members
        # who are not at full health.

        injured_ids = []
        for (i, (name, stats)) in enumerate(self.get_iter(), 1):
            damage  = int(stats["max_health"]) - int(stats["curr_health"])
            if damage >= dmg_thresh:
                injured_ids.append(i)
        return injured_ids