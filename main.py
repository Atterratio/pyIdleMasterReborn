#!/usr/bin/env python3

import os
import sys
import logging
import configparser
import requests
import re
import subprocess
import time
import threading

import bs4

from optparse import OptionParser

parser = OptionParser()
parser.add_option("--debug", action="store_true", dest="debug", default=False, help="Enable debug messanges")
options, args = parser.parse_args()

log = logging.getLogger('Main')
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]: %(message)s')
console = logging.StreamHandler()
console.setFormatter(formatter)
log.addHandler(console)
if options.debug == True:
    log.setLevel(logging.DEBUG)
    sp_out = None
else:
    log.setLevel(logging.INFO)
    sp_out = subprocess.DEVNULL


def main():

    log.info("WELCOME TO PYTHON IDLE MASTER REBORN")
    config = configparser.ConfigParser()
    try:
        config.read_file(open("config.ini"))

        sessionId = config["auth"]["sessionid"]
        if not sessionId:
            log.error("No sessionid set")

        steamLogin = config["auth"]["steamLogin"]
        if not steamLogin:
            log.error("No steamLogin set")

        idleTime = int(config["main"]["idletime"])
        if not idleTime:
            idleTime = 600

        idleThreads = int(config["main"]["idlethreads"])
        if not idleThreads:
            idleThreads = 1

        if not sessionId or not steamLogin:
            sys.exit()

    except FileNotFoundError:
        log.error("No config file. Create empty.")
        config["main"] = {"idletime": 600, "idlethreads": 1}
        config["auth"] = {"sessionid": "", "steamlogin": ""}
        configfile = open('config.ini', 'w')
        config.write(configfile)
        sys.exit()

    myProfileURL = "http://steamcommunity.com/profiles/%s" % steamLogin[:17]

    cookies = {"sessionid": sessionId, "steamLogin": steamLogin}

    myBadgesURL = "%s/badges/" % myProfileURL
    # TODO: catch exceptions
    badges_req = requests.get("%s/badges/" % myProfileURL, cookies=cookies)

    badgePageData = bs4.BeautifulSoup(badges_req.text, "lxml")

    loged = badgePageData.find("a",{"class": "user_avatar"}) != None
    if not loged:
        log.error("Invalid cookie data, cannot log in to Steam")
        sys.exit()

    try:
        badgePages = int(badgePageData.find_all("a",{"class": "pagelink"})[-1].text)
    except IndexError:
        badgePages = 1

    badgeSet = []
    badgesLeft = []
    cardsLeft = 0
    currentpage = 1
    while currentpage <= badgePages:
        badges_req = requests.get("%(url)s?p=%(page)s" % {"url": myBadgesURL, "page": currentpage}, cookies=cookies)
        badgePageData = bs4.BeautifulSoup(badges_req.text, "lxml")
        badgeSet = badgeSet + badgePageData.find_all("div", {"class": "badge_row"})
        currentpage = currentpage + 1

    for badge in badgeSet:
        try:
            dropCount = int(re.findall("\d+", badge.find_all("span",{"class": "progress_info_bold"})[0].get_text())[0])
        except:
            continue

        if dropCount > 0:
            badgeURL = badge.find("a", {"class": "badge_row_overlay"})["href"]
            badgeId = int(re.findall("\d+", badgeURL)[0])
            badgeTitle = badge.find("div", {"class": "badge_title"}).get_text().rsplit("\t", 1)[0].strip()
            badgeData = {"id": badgeId, "url": badgeURL, "title": badgeTitle, "cards": dropCount}

            badgesLeft.append(badgeData)
            cardsLeft += dropCount

    log.info("Idle Master needs to idle %s games for %s cards" % (len(badgesLeft), cardsLeft))

    idleThreads += threading.active_count()
    threads_num = threading.active_count()

    for game in badgesLeft:
        while True:
            threads_num = threading.active_count()
            log.debug("Number of threads: %s" % threads_num)
            if threads_num < idleThreads:
                thread = threading.Thread(target=idle_thread, args=(game, idleTime, cookies))
                thread.start()
                break
            else:
                time.sleep(idleTime // idleThreads)

    while threads_num > 1:
        log.debug("Number of threads: %s" % len(threading.enumerate()))
        time.sleep(idleTime)
        threads_num = len(threading.enumerate())


def idle_thread(game, idleTime, cookies):
        gameId = game["id"]
        badgeURL = game["url"]
        badgeDropLeft = game["cards"]
        gameTitle = game["title"]

        log.info("Starting idle game «%s» to get %s cards" % (gameTitle, badgeDropLeft))

        while badgeDropLeft > 0:
            if sys.platform.startswith('win32'):
                process_idle = subprocess.Popen(["steam-idle.py", str(gameId)], stdout=sp_out,
                                            stderr=sp_out)
            else:
                process_idle = subprocess.Popen(["./steam-idle.py", str(gameId)], stdout=sp_out,
                                                stderr=sp_out)

            log.debug("Idle %02d:%02d min." % divmod(idleTime, 60))
            time.sleep(idleTime)

            log.debug("Check cards left for «%s» game" % gameTitle)
            process_idle.terminate()
            process_idle.communicate()
            time.sleep(15)
            badge_req = requests.get(badgeURL, cookies=cookies)
            badgeRawData = bs4.BeautifulSoup(badge_req.text, "lxml")
            badgeDropLeftOld = badgeDropLeft
            badgeDropLeft = int(re.findall("\d+", badgeRawData.find("span", {"class": "progress_info_bold"}).get_text())[0])
            if badgeDropLeft > 0 and badgeDropLeftOld != badgeDropLeft:
                log.info("Idle game «%s» to get %s cards" % (gameTitle, badgeDropLeft))

        log.info("End «%s» game idle " % gameTitle)


if __name__ == '__main__':
    main()