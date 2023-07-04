
# This module contais functions which extract and manipulate skill 
# information from the HTML source code of the game webpages. 

skill_ids = { # Skill IDs for URLS
    "Rohane": {
        "Critical Attacks": "9101",
        "Damage Increase": "9102",
        "Combat Focus": "9103",
        "Stunning Strikes": "9104",
        "Battle Taunt": "9105",
        "Innate Magic Resistance": "9501",
        "Innate Melee Haste": "9502"
    }
}

def get_skill_id(char_name, skill):

    # This function get the skill ID for the specified character
    # and skill.

    skill_id = skill_ids[char_name][skill]
    return skill_id

def get_unspent_points(soup):

    # This function takes HTML from the skills page and extracts 
    # the number of unspent skill points.

    points_dict = {}
    points_table = soup.select('table[cellspacing="0"][cellpadding="3"][border="0"]')
    strings = list(points_table[0].stripped_strings)
    for (name_string, points) in zip(strings[::3], strings[1::3]):
        name = name_string[2:-2]
        points_dict[name] = points
    return points_dict

def get_skills(soup):

    # This function takes HTML from the skills page and extracts 
    # the number of points that have been spent on each one.

    skill_table = soup.select(
        'table[width="560"][cellspacing="0"][cellpadding="2"][border="0"]'
    )[0]
    rows = skill_table.find_all("tr")
    all_skills = {}
    for row in rows[2:9]:
        skill_dict = {}
        strings = list(row.stripped_strings)[:-1]
        skill = strings[0]
        (skill_dict["points"], skill_dict["level_name"]) = strings[1].split(": ")
        buff_string = (strings[2] if len(strings) == 3 else "(0)")
        skill_dict["buff"] = buff_string[1:-1]
        all_skills[skill] = skill_dict 
    return all_skills

if __name__ == "__main__":
    from bs4 import BeautifulSoup
    with open("html/skills_source.html", "r", encoding = "utf-8") as target:
        soup = BeautifulSoup(target, "html.parser").select(".contentModule.phpGamesNonPortalView")[0]
    print(get_unspent_points(soup))    
