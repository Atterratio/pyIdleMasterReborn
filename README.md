Python Idle Master Reborn
===========

v0.1.5
-------

This program will determine which of your Steam games still have Steam Trading Card drops remaining, and will go through each application to simulate you being “in-game” so that cards will drop.

Many thanks to https://github.com/jshackles for source code to start.

Copy "idle_bot.exp" as "idle_bot.ini" and edit it before start.
I'm not sure that this work on Mac or Windows, or Python2.

* No "GUI"
* MultyGaming

Changes
-------
* Fix Comminity parcing(20180624)
* Fix some crashes

Requirements
-------
* `python3`
* `steam_api` shared libs. You can copy it from installed steam game(for Linux rename it libsteam_api32.so or libsteam_api64.so ).
* `requests`
* `BeautifulSoup`
