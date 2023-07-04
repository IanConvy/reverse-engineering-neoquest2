import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

from . import explore_parser, fight_parser, inventory_parser, skills_parser

# This module contains the Selenium-based driver which is used by the auto-driver 
# to run NeoQuest II, along with a few helper functions. The purpose of this code
# is to interface with Neopets.com, and translate abstracted game actions into 
# specific browser commands and web requests. 

class Driver():

    # This class serves as an intermediate between the game logic in 'game.py' and
    # its associated modules on the one hand, and the Neopets servers on the other.
    # Most of its methods are dedicated to performing specific game actions or updating
    # game state information. 

    def __init__(self, selenium_driver, flag):

        # The core of a Driver instance is the selenium webdriver, which is 
        # initialized seperately in 'main.py'. The 'flag' argument allows for
        # the outer control loop to interact directly with the driver, although
        # this has not been implemented yet.

        self.driver = selenium_driver
        self.source = None
        self.soup = None
        self.skills_dict = None
        self.flag = flag
    
    def get_state_data(self):

        # This method retrieves all relevant game state information by calling
        # a set of more specific information-retrieval methods in an efficient
        # sequence.

        characters_dict = self.get_characters_dict()
        inventory_list = self.get_inventory_list()
        skills_dict = self.get_skills_dict()
        explore_dict = self.get_explore_dict()
        return (explore_dict, characters_dict, inventory_list, skills_dict)
    
    def get_explore_dict(self):

        # This method navigates to the main exploration page and then extracts
        # relevant travel and gold information.

        if not self.is_fighting():
            while self.source != "explore":
                self._return_to_map()
            explore_dict = {
                "area": explore_parser.get_area_name(self.soup),
                "coords": explore_parser.get_location(self.soup),
                "travel_mode": explore_parser.get_travel_mode(self.soup),
                "gold": explore_parser.get_gold(self.soup),
            }
            return explore_dict

    def get_characters_dict(self):

        # This method extracts information about party member status from either
        # the inventory page or the main exploration page, depending on which would
        # require the fewest page loads.

        if not self.is_fighting():
            if self.source == "inventory":
                characters_dict = inventory_parser.get_character_info(self.soup)
            else:
                while self.source != "explore":
                    self._return_to_map()
                characters_dict = explore_parser.get_character_info(self.soup)
            return characters_dict
    
    def get_inventory_list(self):

        # This method navigates to the inventory page and extracts information
        # about the player's inventory items.

        if not self.is_fighting():
            while self.source != "inventory":
                self._open_inventory()
            inventory_list = inventory_parser.get_items(self.soup)
            return inventory_list
        
    def get_skills_dict(self):

        # This method extracts information about the number of unspent
        # skill points and the skill distributions of each character. It
        # tries to be efficient and use prior saved information about skills
        # to avoid loading the skills page unless a skill point was awarded.

        if not self.is_fighting():
            unspent_points = self._get_unspent_points()
            if self.skills_dict is None:
                self.skills_dict = {"skills": {}, "unspent_points": {}}
                for char_name in unspent_points.keys():
                    skills = self._get_char_skills(char_name)
                    self.skills_dict["skills"][char_name] = skills
            self.skills_dict["unspent_points"] = unspent_points
            return self.skills_dict

    def get_fight_dict(self):

        # This method extracts information about the status of a fight, 
        # beginning the fight it has not yet been started.

        while self.source == "fight_start":
            self.begin_fight()
        fight_dict = {
            "players": fight_parser.get_player_stats(self.soup),
            "enemies": fight_parser.get_enemy_stats(self.soup),
            "elapsed_time": fight_parser.get_elapsed_time(self.soup),
            "potions": fight_parser.get_potions(self.soup),
            "abilities": fight_parser.get_abilities(self.soup),
            "messages": fight_parser.get_messages(self.soup),
            "ended": fight_parser.is_ended(self.soup)
        }
        return fight_dict

    def get_fight_end_message(self):

        # This method extracts the ending fight message.

        message = fight_parser.get_end_message(self.soup)
        return message

    def action(self, action):

        # This method executes non-movement actions performed
        # on the main navigation page. The only supported action
        # now is to toggle the travel mode.

        if action in {"normal", "hunting"}:
            self._set_travel_mode(action)

    def move(self, direction):

        # This method makes a move in the specified direction.

        direction_id = explore_parser.get_direction_id(direction)
        if not self.is_fighting():
            while self.source != "explore":
                self._return_to_map()
            self._do_action(
                self.driver.execute_script,
                [f"dosub({direction_id});"],
                "https://www.neopets.com/games/nq2/nq2.phtml"
            )

    def choose_target(self, target_id):

        # This method chooses the specified target during combat.

        id_mapping = self._get_enemy_id_map()
        true_id = id_mapping[target_id]
        self.driver.execute_script(f"settarget({true_id});")

    def wait(self, time):

        # This method performs a wait action for the specified time 
        # during combat.

        self._do_action(
            self.driver.execute_script,
            [f"setaction(6); setparm({time}); document.ff.submit();"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )
    
    def melee_attack(self):

        # This method performs a melee attack.

        self._do_action(
            self.driver.execute_script,
            ["setaction(3); document.ff.submit();"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )
    
    def use_ability(self, ability_name):

        # This method uses the specified ability.

        ability_id = fight_parser.get_ability_id(ability_name)
        self._do_action(
            self.driver.execute_script,
            [f"setaction({ability_id}); document.ff.submit();"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )

    def flee(self):

        # This method attempts to flee a fight.

        self._do_action(
            self.driver.execute_script,
            ["setaction(4); document.ff.submit();"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )
    
    def take_enemy_turn(self):

        # This method allows the enemy to take its turn.

        self._do_action(
            self.driver.execute_script,
            ["setaction(1); document.ff.submit();"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )
    
    def begin_fight(self):

        # This method starts a fight from the initial encounter screen.

        while self.source == "fight_start":
            self._do_action(
                self.driver.get,
                ["https://www.neopets.com/games/nq2/nq2.phtml?start=1"],
                "https://www.neopets.com/games/nq2/nq2.phtml"
            )

    def end_fight(self):

        # This method ends a fight after the final turn.

        while self.source == "fight":
            self._do_action(
                self.driver.execute_script,
                ["setaction(2); document.ff.submit();"],
                "https://www.neopets.com/games/nq2/nq2.phtml"
            )

    def return_from_fight(self):

        # This method returns to the main navigation page from the
        # loot screen.

        while self.source == "fight_end":
            self._do_action(
                self._fight_return,
                [],
                "https://www.neopets.com/games/nq2/nq2.phtml"
            )

    def use_fight_potion(self, potion_name):

        # This method uses a potion during combat.

        potion_id = inventory_parser.get_potion_id(potion_name)
        self._do_action(
            self.driver.execute_script,
            [f"setaction(5); setitem({potion_id}); document.ff.submit();"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )

    def drink_inventory_potion(self, potion_name, char_id):

        # This method uses a potion outside of combat.

        potion_id = inventory_parser.get_potion_id(potion_name)
        url = f"https://www.neopets.com/games/nq2/nq2.phtml?act=inv&iact=use&targ_item={potion_id}&targ_char={char_id}"
        self._do_action(
            self.driver.get,
            [url],
            "https://www.neopets.com/games/nq2/nq2.phtml?act=inv"
        )

    def upgrade_skill(self, char_name, skill, points):

        # This method spends a specfied number of skill points on the
        # selected skill.

        skill_id = skills_parser.get_skill_id(char_name, skill)
        char_id = explore_parser.get_character_id(char_name)
        url = f"https://www.neopets.com/games/nq2/nq2.phtml?act=skills&buy_char={char_id}&confirm=1&skopt_{skill_id}={points}"
        self._do_action(
            self.driver.get,
            [url],
            "https://www.neopets.com/games/nq2/nq2.phtml?act=skills"
        )
        skills = self._get_char_skills(char_name)
        self.skills_dict["skills"][char_name] = skills

    def reset_game(self):

        # This method resets the game.

        while self.source != "intro":
            self._do_action(
                self.driver.get,
                ["https://www.neopets.com/games/nq2/nq2.phtml?restart=1"],
                "https://www.neopets.com/games/nq2/nq2.phtml"
            )
        while not is_restarted(self.soup):
            self._do_action(
                self.driver.get,
                ["https://www.neopets.com/games/nq2/nq2.phtml?startgame=1"],
                "https://www.neopets.com/games/nq2/nq2.phtml"
            )

    def is_fighting(self):

        # This method returns true if a fight is occurring.

        check = self.source and ("fight" in self.source)
        return check

    def _get_unspent_points(self):

        # This internal method extracts the number of unspent skill points
        # from either the inventory or skill screens.

        if not self.is_fighting():
            if self.source == "inventory":
                unspent_points = inventory_parser.get_unspent_points(self.soup)
            else:
                while "skills" not in self.source:
                    self._open_skills()
                unspent_points = skills_parser.get_unspent_points(self.soup)
            return unspent_points

    def _set_travel_mode(self, mode):

        # This internal method sets the specified travel mode.

        mode_id = (2 if mode == "hunting" else 1)
        self._do_action(
            self.driver.get,
            [f"https://www.neopets.com/games/nq2/nq2.phtml?act=travel&mode={mode_id}"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )

    def _return_to_map(self):

        # This internal method navigates back to the main game page.

        self._do_action(
            self.driver.get,
            ["https://www.neopets.com/games/nq2/nq2.phtml"],
            "https://www.neopets.com/games/nq2/nq2.phtml"
        )

    def _open_inventory(self):

        # This internal method navigates to the inventory page.

        self._do_action(
            self.driver.get,
            ["https://www.neopets.com/games/nq2/nq2.phtml?act=inv"],
            "https://www.neopets.com/games/nq2/nq2.phtml?act=inv"
        )

    def _open_skills(self, char_name = None):

        # This internal method navigates to the skills page.

        char_name = ("Rohane" if char_name is None else char_name)
        char_id = explore_parser.get_character_id(char_name)
        self._do_action(
            self.driver.get,
            [f"https://www.neopets.com/games/nq2/nq2.phtml?act=skills&show_char={char_id}"],
            f"https://www.neopets.com/games/nq2/nq2.phtml?act=skills&show_char={char_id}"
        )

    def _get_char_skills(self, char_name):

        # This internal method extracts the skills and spent skill points
        # for a specified character.

        if not self.is_fighting():
            while self.source != f"skills_{char_name}":
                self._open_skills(char_name)
            skills = skills_parser.get_skills(self.soup)
            return skills

    def _get_enemy_id_map(self):

        # This internal method constructs a map between the apparent left-to-right
        # ID numbering starting from five, and the actual ID numbering on the server
        # (which sometimes differs from the expected pattern).

        enemy_ids = fight_parser.get_enemy_ids(self.soup)
        id_map = {str(i):enemy_id for (i, enemy_id) in enumerate(enemy_ids, 1)}
        return id_map

    def _fight_return(self):

        # This internal method finishes a fight either in victory or defeat.

        defeated_button = self.driver.find_elements(
            By.CSS_SELECTOR, 'input[value="Return to your last rest spot..."]'
        )
        if defeated_button:
            defeated_button[0].click()
        else:
            self.driver.get("https://www.neopets.com/games/nq2/nq2.phtml?finish=1")

    def _get_page_soup(self):

        # This internal method gets the page HTML from the Selenium driver and returns
        # a BeautifulSoup object.

        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        game_elements = soup.select(".contentModule.phpGamesNonPortalView")[0]
        return game_elements

    def _do_action(self, func, args, safe_url):

        # This internal method performs the action specified by 'func' in a manner
        # that can tolerate unresponsiveness from the Neopets servers. The method
        # waits until the previous game div tag becomes stale and then reloads. If
        # the page fails to reload, the browser will be directed off of and then onto
        # Neopets.com, forcing a refresh of the page. After confirming that the page has
        # been loaded, the new HTML and page type are both saved. The 'safe_url' is a URL
        # that the browser can safely return to without breaking continuity in the game logic.

        while True:
            try: # Try to reload page naturally
                game_div = self.driver.find_element(
                    By.CSS_SELECTOR, ".contentModule.phpGamesNonPortalView"
                )
                func(*args)
                WebDriverWait(self.driver, 20).until(staleness_of(game_div))
                WebDriverWait(self.driver, 20).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, ".contentModule.phpGamesNonPortalView")
                )
                break
            except TimeoutException:
                print("Action failed.")
                while True: # Force a reload by navigating off of Neopets.com and then returning
                    try:
                        self._hard_refresh(safe_url)
                        break
                    except TimeoutException:
                        pass
        self.soup = self._get_page_soup()
        self.source = get_source(self.soup)
        time.sleep(0.3)

    def _hard_refresh(self, return_url):

        # This internal method will navigate to google.com and then
        # return to the specified URL.

        self.driver.get("https://www.google.com/")
        WebDriverWait(self.driver, 20).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "img.lnXdpd")
        )
        self.driver.get(return_url)
        WebDriverWait(self.driver, 20).until(
            lambda d: d.find_element(By.CSS_SELECTOR, ".contentModule.phpGamesNonPortalView")
        )
    
    def _log_local_map(self, conn):

        # This internal method logs the images that are used in map display. This
        # information is not currently used by the auto-player, but it is still
        # worthwhile to collect.

        if not self.is_fighting():
            while self.source != "explore":
                self._return_to_map()
            area = explore_parser.get_area_name(self.soup)
            map_dict = explore_parser.get_local_map(self.soup)
            cursor = conn.cursor()
            for ((x_pos, y_pos), image) in map_dict.items():
                cursor.execute(
                    """
                    INSERT INTO map (area, x_pos, y_pos, image)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT (area, x_pos, y_pos, image)
                        DO NOTHING;
                    """, (area, x_pos, y_pos, ",".join(image))
                )
            cursor.close()
            conn.commit()

def get_source(soup):

    # This function takes the provided soup object and determines
    # the type of game page that it corresponds to.

    source = None
    if soup.select("map"):
        source = "explore"
    elif soup.find_all(string = "- Inventory and Party Info -"):
        source = "inventory"
    elif soup.find_all(string = "- Character Skills -"):
        for char_name in ["Rohane", "Mispy", "Talinia", "Velm", "Invalid"]:
            if soup.find_all(string = f"- {char_name}'s Skills -"):
                break
        source = f"skills_{char_name}"
    elif soup.find_all(string = re.compile("You are attacked by.*")):
        source = "fight_start"
    elif soup.select('input[name="target"]'):
        source = "fight"
    elif soup.select(
        'a[href="nq2.phtml?finish=1"], input[value="Return to your last rest spot..."]'):
        source = "fight_end"
    elif soup.find_all(string = re.compile("nearing the end of his reign")):
        source = "intro"
    return source

def is_restarted(soup):

    # This function returns true if its the first move after a reset.

    check = bool(soup.find_all(string = re.compile("be careful out there!")))
    return check

def are_unspent(unspent_points):

    # This function returns true if there are unspent skill points in the
    # passed skill dictionary.

    check = any(tupl[1] != "0" for tupl in unspent_points.items())
    return check