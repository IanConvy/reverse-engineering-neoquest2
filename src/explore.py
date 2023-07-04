
# This module contains all classes and functions which involve
# map locations.

class ExploreState():

    # This structure holds information about player location,
    # travel mode, and gold.

    def __init__(self, explore_dict):

        # 'explore_dict' is the data structure returned by the 
        # auto-player driver's `get_explore_dict` method.

        self.area = explore_dict["area"]
        self.coords = explore_dict["coords"]
        self.travel_mode = explore_dict["travel_mode"]
        self.gold = explore_dict["gold"]

def compute_direction(coords1, coords2):

    # This function calculates the direction that would be 
    # needed to move from 'coords1' to 'coords2'. If the two
    # coordinate sets are not adjacent, then the function
    # returns an empty string.

    x_diff = int(coords2[0]) - int(coords1[0])
    y_diff = int(coords2[1]) - int(coords1[1])
    if abs(x_diff) > 1 or abs(y_diff) > 1:
        return ""
    if x_diff == 1:
        x_str = "s"
    elif x_diff == -1:
        x_str = "n"
    else:
        x_str = ""
    if y_diff == 1:
        y_str = "e"
    elif y_diff == -1:
        y_str = "w"
    else:
        y_str = ""
    direction = x_str + y_str
    return direction

def simulate_move(coords, direction):

    # This function returns coordinates for the map tile 
    # which would be reached if the player moved in `direction` 
    # starting from `coords`. 

    (x_0, y_0) = tuple(map(int, coords))
    if "n" in direction:
        x_1 = x_0 - 1
    elif "s" in direction:
        x_1 = x_0 + 1
    else:
        x_1 = x_0
    if "w" in direction:
        y_1 = y_0 - 1
    elif "e" in direction:
        y_1 = y_0 + 1
    else:
        y_1 = y_0
    return (str(x_1), str(y_1))

def get_opposite_direction(direction):

    # This function retuns the direction which points
    # opposite to the passed direction.

    new_direction = ""
    for char in direction:
        if char == "n": 
            new_direction += "s"
        elif char == "s":
            new_direction += "n"
        elif char == "e":
            new_direction += "w"
        elif char == "w":
            new_direction += "e"
    return new_direction
