# Reverse Engineering NeoQuest II

This repository documents my ongoing efforts to reverse engineer a web-based game called NeoQuest II. I employ
a Selenium-based Python program to play through the game autonomously, logging large quantities of data that
I can then analyze using R to extract different game mechanics.

Although the code in this repository is not intended as a fully-fledged application or library, it is documented and can be easily run in an
environment with Python and R. The only external dependencies of the auto-player are [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) for HTML parsing and [Selenium](https://pypi.org/project/selenium/) for browser
automation.

A comprehensive write-up of my motivation, methodology, and preliminary findings can be found on [my website](https://ianconvy.github.io/projects/other/neoquest/neoquest.html).
