import time
import yaml

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from src import game, config
from src.neopets import neo_driver

# The code in this file initializes the Selenium webdriver and 
# then starts the NeoQuest II auto-player. The user must login 
# to Neopets.com using their own credentials in order for the 
# game to run.

def get_firefox():

    # This function initializes a Firefox browser using Selenium,
    # attempts to install the uBlock Origin extension (not included),
    # and then navigates to the NeoQuest II page.

    options = Options()
    options.page_load_strategy = "none"
    driver = webdriver.Firefox(options = options)
    try:
        driver.install_addon("ublock_origin-1.50.0.xpi")
    except:
        pass
    driver.get("https://www.neopets.com/games/nq2/nq2.phtml")
    return driver

def run_automatic(selenium_driver, schedule, logging):

    # This function runs the auto-players main game loop in
    # automatic mode, which allows the user to halt operation
    # by typing "kill".

    flag = [True]
    callback = None
    driver = neo_driver.Driver(selenium_driver, flag)
    game_thread = game.GameThread(flag, driver, schedule, logging = logging, callback = callback)
    game_thread.start()
    while game_thread.is_alive():
        action = input("Control: ")
        if action == "kill":
            flag[0] = False
        time.sleep(1)

def run_manual(selenium_driver, schedule, logging):

    # This function runs the auto-player in manual mode. At this
    # level of code, the only difference is that the game loop does
    # not listen for a kill command from the user.

    flag = [True]
    callback = None
    driver = neo_driver.Driver(selenium_driver, flag)
    game_thread = game.GameThread(flag, driver, schedule, logging = logging, callback = callback)
    game_thread.start()
    while game_thread.is_alive():
        time.sleep(1)

if __name__ == "__main__":

    # When this file is executed as a top-level script, it initializes
    # the auto-player and then waits for the user to singal that they
    # have signed in before starting the game loop with the configuration
    # specified in `config.yml`.

    with open("config.yml", "r", encoding = "utf-8") as target:
        config_dict = yaml.safe_load(target)
    driver = get_firefox()
    input("Login (press enter to continue)")
    schedule = config.Schedule(config_dict)
    logging = config_dict["log"]
    if config_dict["manual"]:
        run_manual(driver, schedule, logging)
    else:
        run_automatic(driver, schedule, logging)
    driver.quit()