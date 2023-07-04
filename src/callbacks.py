from . import explore

# This module holds arbitrary functions that can be passed
# to the auto-player and called at the beginning of each game 
# loop iteration. When called, the functions are passed the
# GameState instance at the start of the step.

class PathLogger():

    # This callback will log the path that the auto-player takes
    # through the game world, tile by tile.

    def __init__(self, save_path):

        # 'save_path' specifies where the log should be saved

        self.coord_hist = []
        self.directions = []
        self.save_path = save_path
    
    def __call__(self, game_state):

        # When the instance is called, it extracts the current
        # map coordinates, stores them, and then writes them to the
        # log file. After the first move, it begin to log the direction
        # of movements by computing the difference between the new 
        # coordinates and the previous coordinates. If the direction
        # is ambiguous, the user will be prompted to manually input it.

        area = game_state.explore.area
        coords = game_state.explore.coords
        self.coord_hist.append((area, coords))
        if len(self.coord_hist) > 1:
            (old_area, old_coords) = self.coord_hist[-2]
            direction = explore.compute_direction(old_coords, coords)
            if area != old_area or not direction:
                overide = input("Direction overide?: ")
                direction = overide if overide else direction
            self.directions.append(direction)
            with open(self.save_path, "a", encoding = "utf-8") as target:
                target.write(f"{direction}\n{area}|{coords[0]}|{coords[1]}|")
        else:
            with open(self.save_path, "a", encoding = "utf-8") as target:
                target.write(f"{area}|{coords[0]}|{coords[1]}|")
