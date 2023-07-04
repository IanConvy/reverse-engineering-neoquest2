
# This module contains the SkillSchedule class, which 
# handles the assignment of skill points.

class SkillSchedule():

    # This handler will spend skill points based on the specified
    # skill schedule.

    def __init__(self, schedule_dict):

        # The 'schedule_dict' dictionary must have the form
        # '{char_name: [(skill_name, points), ...], ...}', where
        # 'skill_name' and 'points' denote how many points should be 
        # assigned to 'skill_name' before moving to the next tuple
        # in the list.

        self.schedule_dict = {}
        self.steps = {}
        for (char_name, schedule_list) in schedule_dict.items():
            parsed_schedule = parse_skill_schedule(schedule_list)
            self.schedule_dict[char_name] = parsed_schedule
            self.steps[char_name] = 0
    
    def perform(self, game_state):

        # This method spends any unspent skill points on next skill
        # in the schedule, until the specified point threshold for that 
        # skill is reached. After that, the schedule is advanced to the 
        # next tuple, and the process is repeated. 

        action = "nothing"
        for (char_name, points) in game_state.skills.unspent.items():
            step = self.steps.get(char_name, 0)
            schedule = self.schedule_dict.get(char_name, [])
            if (int(points) > 0) and (step < len(schedule)):
                (skill, add_points) = schedule[step]
                action = f"{char_name}_{skill}_{add_points}"
                self.steps[char_name] += 1
                break
        return action

def parse_skill_schedule(schedule):

    # This function flattens a user-provided skill schedule
    # into a schedule with duplicated tuples that contain
    # only a single skill point.

    skill_list = []
    for (skill_name, num_points) in schedule:
        skill_list += [(skill_name, 1)] * num_points
    return skill_list