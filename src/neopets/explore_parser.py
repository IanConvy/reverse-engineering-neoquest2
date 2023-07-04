import re

# This module contais functions which extract and manipulate information 
# from the HTML source code on the main navigation page. 

direction_ids = { # IDs for JavaScript movement commands
    "n": 1,
    "s": 2,
    "w": 3,
    "e": 4,
    "nw": 5,
    "sw": 6,
    "ne": 7,
    "se": 8
}

char_ids = { # IDs for the four party members
    "Rohane": "1",
    "Mipsy": "2",
    "Talinia": "3",
    'Velm': "4"
}

def parse_coord_attrs(td_tag):

    # This function gets coordinates from HTML tags in the
    # game map image.

    attrs = list(td_tag.attrs.keys())
    x = attrs[0].split("(")[-1][:-1]
    y = attrs[1].split(")")[0]
    return (x, y)

def get_location(soup):

    # This function takes HTML from the navigation page and
    # uses the location of Rohane's image to identify the
    # location of the player.

    td_tag = soup.select(
        'td:has(> div > :is([src*="a2_5596a"], [src*="a1_b87f3"]))')[0]
    coords = parse_coord_attrs(td_tag)
    return coords

def get_area_name(soup):

    # This function extracts the region name from the page HTML.

    location_string = str(soup.find(string = re.compile("You are.*"))).strip()
    location = location_string[11:].split(".")[0]
    return location

def get_travel_mode(soup):

    # This function extracts the travel mode from the page HTML.

    bolded_text = {str(tag.string) for tag in soup.find_all("b")}
    if "Normal" in bolded_text:
        travel = "normal"
    else:
        travel = "hunting"
    return travel

def get_local_map(soup):

    # This function extracts the tile images from the navigation map HTML.

    map_dict = {}
    map_cells = soup.select('td:has(> div > img[src^="//images.neopets.com/nq2/t/"])')
    for td_tag in map_cells:
        coords = parse_coord_attrs(td_tag)
        imgs = td_tag.div.select("img")
        images = [img_tag["src"] for img_tag in imgs]
        map_dict[coords] = images
    return map_dict

def get_character_info(soup):

    # This function extracts information the level, experience and
    # hitpoints of all party members.

    info_dict = {}
    char_table = soup.select(
        'table[width="560"][border="0"][cellspacing="0"][cellpadding="0"]'
    )[0]
    char_rows = char_table.tbody.find_all("tr", recursive = False)[1:]
    for row in char_rows:
        char_dict = {}
        cells = row.find_all("td", recursive = False)
        name = str(cells[0].string).strip()
        char_dict["level"] = str(cells[1].string).strip()
        (char_dict["curr_health"], char_dict["max_health"]) = str(cells[4].string).strip().split("/")
        char_dict["exp"] = str(cells[6].string).strip()
        info_dict[name] = char_dict
    return info_dict

def get_gold(soup):

    # This function extracts the amount of gold the player has.

    start_text = soup.find(string = re.compile("You have .*"))
    gold_amount = str(start_text.next_sibling.string)
    return gold_amount

def get_character_id(name):

    # This function gets the ID of a specified party member.

    char_id = char_ids[name]
    return char_id

def get_direction_id(direction):

    # This function get the ID of a specified direction.

    direction_id = direction_ids[direction]
    return direction_id