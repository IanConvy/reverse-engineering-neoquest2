
# This module contais functions which extract and manipulate information 
# from the HTML source code during combat. 

ability_ids = { # IDs for JavaScript ability commands
    "Combat Focus": 9103,
    "Battle Taunt": 9105
}

def get_elapsed_time(soup):

    # This function extracts the amount of time that has elepased in
    # a fight.

    strings = list(soup.stripped_strings)[1:]
    elapsed_time = strings[-1]
    return elapsed_time

def get_enemy_ids(soup):

    # This function extracts enemy IDs, which do not always start at 5.

    table_tag = soup.select("center > table > tbody > tr > td > table > tbody")[0]
    img_row = table_tag.find("tr", recursive = False)
    enemy_profiles = img_row.select("div")
    enemy_ids = [([""] + [tag["name"][-1] for tag in pr.select("img[name]")])[-1]
                 for pr in enemy_profiles]
    return enemy_ids

def get_enemy_stats(soup):

    # This function extracts the name, hitpoints, buffs, and time until next move 
    # for each enemy.

    table_tag = soup.select("center > table > tbody > tr > td > table > tbody")[0]
    rows = table_tag.find_all("tr", recursive = False)
    enemy_names = list(rows[2].stripped_strings)
    enemy_cells = rows[4].select('td[valign="top"][align="center"]')
    stat_strings = [list(tag.stripped_strings) for tag in enemy_cells]
    curr_hitpoints = [strings[0].split("/")[0] for strings in stat_strings]
    max_hitpoints = [strings[0].split("/")[1] for strings in stat_strings]
    time_strings_raw = [([""] + [time for time in strings[1:3] if " sec" in time or time == "now"])[-1]
                        for strings in stat_strings]
    time_strings = [string.split("Next turn: ")[-1] for string in time_strings_raw]
    status_strings = ["|".join([string for string in strings[2:] if string != "now"])
                      for strings in stat_strings]
    enemy_dict = {}
    for i in range(len(enemy_names)):
        enemy_dict[i + 1] = {
            "name": enemy_names[i], "curr_health": curr_hitpoints[i],
            "max_health": max_hitpoints[i], "time": time_strings[i],
            "buff": status_strings[i]
        }
    return enemy_dict

def get_player_stats(soup):

    # This function extracts the name, hitpoints, buffs, and time until next move 
    # for each party member.

    table_tag = soup.select("center > table > tbody > tr > td > table > tbody")[-1]
    rows = table_tag.find_all("tr", recursive = False)
    name_health_strings = list(rows[0].stripped_strings)
    player_names = name_health_strings[::2]
    curr_health = [string.split("/")[0] for string in name_health_strings[1::2]]
    max_health = [string.split("/")[1] for string in name_health_strings[1::2]]
    time_status_tags = rows[3].select('td[valign="top"][align="center"]')
    time_status_strings = [list(tag.stripped_strings) for tag in time_status_tags]
    time_strings_raw = [([""] + [time for time in strings[:2] if " sec" in time or time == "now"])[-1]
                        for strings in time_status_strings]
    time_strings = [string.split("Next turn: ")[-1] for string in time_strings_raw]
    status_strings = ["|".join([string for string in strings[1:] if string != "now"])
                      for strings in time_status_strings]
    player_dict = {}
    for (i, name) in enumerate(player_names):
        player_dict[name] = {
            "name": name, "curr_health": curr_health[i],
            "max_health": max_health[i], "time": time_strings[i],
            "buff": status_strings[i]
        }
    return player_dict
        
def get_potions(soup):

    # This function extracts the type and quantity of potions available 
    # during combat.

    potion_dict = {}
    potion_table = soup.select('table[width="100%"]')[0]
    potion_strings = list(potion_table.tbody.tr.td.stripped_strings)
    for (quant, name) in zip(potion_strings[::5], potion_strings[1::5]):
        potion_dict[name] = quant
    return potion_dict

def get_abilities(soup):

    # This function extracts the abilities available to a character during
    # their turn.

    abilities_list = []
    ability_table = soup.select('table[width="100%"]')[0]
    ability_cell = ability_table.tbody.tr.find_all("td", recursive = False)[1]
    for link_tag in ability_cell.select("a"):
        abilities_list.append(str(link_tag.string).strip())
    return abilities_list

def get_messages(soup):

    # This function extracts the messages which describe actions that were
    # taken in the previous turn.

    message_cell = soup.select('td[width="*"]')[0]
    message_string = " ".join(message_cell.stripped_strings)
    return message_string

def get_end_message(soup):

    # This function extracts the message displayed at the end of the fight.

    all_strings = list(soup.stripped_strings)
    messages = " ".join(all_strings[1:])
    return messages

def is_ended(soup):

    # This function returns true if the fight has ended.

    ended = bool(soup.select('img[src$="com_end.gif"]'))
    return ended

def get_ability_id(ability_string):

    # Thos function gets the ID for the specified ability.

    for (ability_type, ability_id) in ability_ids.items():
        if ability_type in ability_string:
            return ability_id

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    with open("html/fight_source.html", "r", encoding = "utf-8") as target:
        soup = BeautifulSoup(target, "html.parser").select(".contentModule.phpGamesNonPortalView")[0]
    print(get_enemy_ids(soup))
    print(get_player_stats(soup))
    print(get_enemy_stats(soup))    