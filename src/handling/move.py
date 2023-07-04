import random

from .. import explore

# This module contains move handler classes with different
# patterns of behavior, plus some associated helper functions.

locations = { # Dictionary of important map coordinates
    "White River": ("the Northern Marches", "16", "54")
}

class MoveHandler():

    # The base move handler class.

    def __init__(self):
        pass

    def perform(self):

        # This method is called by the auto-player to gets its
        # next move.

        pass

    def reset(self):

        # This method resets the state of the move handler.

        pass

class MoveChain(MoveHandler):

    # This handler consists of a sequence of other move handlers,
    # along with an optional set of custom release conditions.

    def __init__(self):
        self.handlers = []
        self.releasers = []
        self.stage = 0
        self.length = 0
        self.cycle = False

    def add(self, handler, release_function = None):

        # This method appends a new move handler to the handler chain,
        # along with a function that takes the GameState instance and 
        # returns a boolean value indicating if the current handler
        # should be released. Note that this new release condition will
        # be used in addition to the original release condition of the
        # component handler, as if an OR operation were done between
        # them.

        if release_function is None:
            def release_function(game_state): return False
        self.releasers.append(release_function)
        self.handlers.append(handler)
        self.length += 1

    def perform(self, game_state):

        # This method queries the current move handler in the chain to
        # get an action. If the handler's release condition is satisfied,
        # then the next handler is activated and queried. If no handlers 
        # remain and 'self.cycle' is not true, then the MoveChain instance
        # as a whole will release.

        if self.stage >= self.length:
            if self.cycle:
                self.reset_handlers()
                self.stage = 0
                action = self.perform(game_state)
            else:
                action = "release"
        else:
            release_function = self.releasers[self.stage]
            if release_function(game_state):
                self.stage += 1
                action = self.perform(game_state)
            else:
                handler = self.handlers[self.stage]
                action = handler.perform(game_state)
                if action == "release":
                    self.stage += 1
                    action = self.perform(game_state)
        return action
    
    def cycle_handlers(self):

        # If this method is called, the MoveChain instance will
        # loop its handler sequence instead of releasing at the end.

        self.cycle = True

    def reset_handlers(self):

        # This method resets the states of all handlers in the chain.

        for handler in self.handlers:
            handler.reset()

class PathFollow(MoveHandler):

    # This handler follows a specified path saved in an external file, and will
    # release once it reaches the end of that path.

    def __init__(self, file_path, reverse = False):

        # Steps in the file path are assumed to have the form "region|height|width|direction",
        # where "height" and "width" are the first and second map tile coordinates respectively.

        with open(file_path, "r", encoding = "utf-8") as target:
            path = [tuple(string.strip().split("|")) for string in target.readlines()]
        self.moves = {tupl[:3]: tupl[3] for tupl in path}
        if reverse:
            self.moves = reverse_moves(self.moves)

    def perform(self, game_state):

        # The handler will automatically detect the player's position on the path,
        # and return the next direction. If the player has somehow left the path, the
        # handler will attempt to return to it.

        current_coords = (game_state.explore.area,) + game_state.explore.coords
        action = self.moves.get(current_coords)
        if action is None:
            action = self.recover(current_coords)
        elif action == "":
            action = "release"
        return action
    
    def recover(self, coords):

        # This method tries to get the player back on the path by looking for an
        # adjacent tile that is on the path and moving to it. If there is no such
        # tile, the handler will release.

        action = "release"
        for cand_action in ["n", "s", "e", "w", "nw", "ne", "sw", "se"]:
            next_coords = coords[0:1] + explore.simulate_move(coords[1:], cand_action)
            if self.moves.get(next_coords) is not None:
                action = cand_action     
        return action

class Pivot(MoveHandler):

    # This handler will move between two map tiles indefinitely.

    def __init__(self, direction):

        # The 'direction' argument specifies how the handler should
        # initially move once it is activated. After making this move,
        # it will return to the original tile by moving in the opposite
        # direction.

        self.direction = direction
        self.opposite = explore.get_opposite_direction(direction)
        self.count = 1
        self.prev_coords = None

    def perform(self, game_state):

        # The handler will move in the specified direction on even
        # move counts, and move in the opposite direction on odd 
        # move counts.

        new_coords = game_state.explore.coords
        if new_coords != self.prev_coords:
            self.prev_coords = new_coords
            self.count += 1
        if self.count % 2 == 1:
            action = self.opposite
        else:
            action = self.direction
        return action

class RandomWalk(MoveHandler):

    # This handler will move in random directions, selected uniformly,
    # forever. However, it can be instructed to avoid specific map tiles.

    def __init__(self, avoid = []):

        # The avoid argument is a list of coordinates that the handler
        # will not move to.

        self.avoid = set(avoid)

    def perform(self, game_state):
        coords = game_state.explore.coords
        action = random.choice(["n", "s", "e", "w", "ne", "nw", "se", "sw"])
        next_coords = explore.simulate_move(coords, action)
        if next_coords in self.avoid:
            action = self.perform(game_state)
        return action

class ExplorePrompt(MoveHandler):
    
    # This handler is used for manual control of the auto-player
    # by the user.

    def perform(self, game_state):
        valid = False
        while not valid:
            action = input("Action: ")
            if action in {
                    "n", "s", "e", "w", "ne", "nw", "se", "sw", "release"}:
                valid = True
            else:
                print("Invalid action.")
        return action

class ToggleMode(MoveHandler):

    # This handler will activate the specified travel mode,
    # and then release.

    def __init__(self, mode):

        # 'mode' can either be "normal" or "hunting"

        self.mode = mode
        self.active = True

    def perform(self, game_state):
        if self.active:
            action = self.mode
            self.active = False
        else:
            action = "release"
        return action
    
    def reset(self):

        # The handler must be reset in order to set the mode
        # again.

        self.active = True

def location_release(area, coords):

    # This function returns a release function for MoveChain that
    # checks if the player has moved to the specified coordinates.

    def release_func(game_state):
        area_check = (game_state.explore.area == area)
        coord_check = (game_state.explore.coords == coords)
        release = (area_check and coord_check)
        return release
    return release_func

def reverse_moves(move_dict):

    # This function will reverse a path that has been loaded into a 
    # PathFollow handler. Note that it will not work correctly if 
    # the coordinate basis changes across the path.

    coords = reversed(move_dict.keys())
    directions = [explore.get_opposite_direction(direction)
                  for direction in reversed(move_dict.values())
                  if direction] + [""]
    reversed_moves = {coord:direction for (coord, direction) in zip(coords, directions)}
    return reversed_moves

if __name__ == "__main__":
    handler = PathFollow("paths/zombom", reverse = True)
    for ((area, x, y), direction) in handler.moves.items():
        print(f"{area}|{x}|{y}|{direction}")