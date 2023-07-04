
# This module contains all classes and functions which involve
# skills.

class SkillsState():

    # This structure contains the skills of all party members
    # at a given game step.

    def __init__(self, skills_dict):

        # 'skills_dict' is the data structure returned by the 
        # auto-player driver's `get_skills_dict` method.

        self.skills = skills_dict["skills"]
        self.unspent = skills_dict["unspent_points"]

    def __getitem__(self, char_name):
        level = self.skills[char_name]
        return level
    
    def get_iter(self):
        itr = self.skills.items()
        return itr
