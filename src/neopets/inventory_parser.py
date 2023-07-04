
# This module contais functions which extract and manipulate inventory 
# information from the HTML source code of the game webpages. 

potion_ids = { # Potion IDs for URLS
    "Healing Vial": "30011",
    "Healing Flask": "30012",
    "Healing Potion": "30013",

    "Flare Potion": "30100"
}

def get_potion_id(name):

    # This functions gets the ID for the specified
    # potion.

    potion_id = potion_ids.get(name)
    return potion_id

def get_items(soup):

    # This function takes HTML from the inventory page and 
    # extracts all item names, quantities, and buffs in the 
    # player's inventory. It also detects which items are
    # equipped by party members.

    all_items = []
    item_table = soup.select(
        'table[width="560"][cellspacing="0"][cellpadding="3"][border="0"]'
    )[0]
    rows = item_table.tbody.find_all("tr")
    for row in rows[1:]:
        item_dict = {}
        cells = row.find_all("td")
        name_string = list(cells[0].stripped_strings)
        item_dict["name"] = name_string[0]
        item_dict["buffs"] = list(zip(name_string[1::2], name_string[2::2]))
        quant_tag = cells[1].b
        item_dict["quant"] = quant_tag.string.strip() if quant_tag else ""
        item_dict["type"] = " ".join(cells[2].stripped_strings)
        if "Unequip" in set(cells[3].stripped_strings):
            item_dict["equipped"] = True
        else:
            item_dict["equipped"] = False
        all_items.append(item_dict)
    return all_items

def get_character_info(soup):

    # This function takes HTML from the inventory page and returns info
    # about the status of the party members.

    char_table = soup.select('table[width="560"][cellspacing="0"][cellpadding="0"][border="0"]')[0]
    strs = list(char_table.stripped_strings)
    characters_dict = {}
    for (name, hp_string, level, exp) in zip(strs[::12], strs[3::12], strs[7::12], strs[9::12]):
        (curr_health, max_health) = hp_string.split("/")
        characters_dict[name] = {"level": level, "curr_health": curr_health, "max_health": max_health, "exp": exp}
    return characters_dict

def get_unspent_points(soup):

    # This function takes HTML from the inventory page and extracts 
    # the number of unspent skill points.

    char_table = soup.select('table[width="560"][cellspacing="0"][cellpadding="0"][border="0"]')[0]
    strs = list(char_table.stripped_strings)[:-4]
    points_dict = {}
    for (name, point_string) in zip(strs[::12], strs[1::12]):
        points = point_string.split(" skill")[0]
        points_dict[name] = points
    return points_dict

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    with open("html/inventory_source.html", "r", encoding = "utf-8") as target:
        soup = BeautifulSoup(target, "html.parser").select(".contentModule.phpGamesNonPortalView")[0]
    print(get_unspent_points(soup))    