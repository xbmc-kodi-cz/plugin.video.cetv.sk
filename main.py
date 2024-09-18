# -*- coding: utf-8 -*-
# Module: default
# Author: rywko
# Created on: 15.11.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import re
import sys
from collections import OrderedDict
from urllib.parse import urlencode, parse_qsl

import urllib3
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
# from html.parser import HTMLParser
from bs4 import BeautifulSoup

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
_addon_ = xbmcaddon.Addon('plugin.video.cetv.sk')
_scriptname_ = _addon_.getAddonInfo('name')
home = _addon_.getAddonInfo('path')

FEEDS = OrderedDict([
    ('Spravodajstvo', 'http://cetv.sk/category/archiv/spravodajstvo/'),
    ('Publicistika', 'http://cetv.sk/category/archiv/publicistika/'),
    ('Šport', 'http://cetv.sk/category/archiv/sport/'),
    ('Relácie', 'http://cetv.sk/category/archiv/relacie/')
])


def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__ == 'unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s" % (_scriptname_, msg.__str__()), level)


def logN(msg):
    log(msg, level=xbmc.LOGINFO)


# def fetchUrl(url, label):
#     logN("fetchUrl " + url + ", label:" + label)
#     httpdata = ''
#     req = urllib.request.Request(url)
#     req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0')
#     resp = urllib.request.urlopen(req)
#     httpdata = resp.read().decode('utf-8')
#     resp.close()
#     return httpdata

def search(page):
    user_agent = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"}
    http = urllib3.PoolManager(1, headers=user_agent)
    return http.request("GET", page).data.decode("utf-8")


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    xbmcplugin.setContent(_handle, 'videos')
    for category in FEEDS.keys():
        list_item = xbmcgui.ListItem(label=category)
        url = get_url(action='listing', url=FEEDS[category])
        # is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
        logN("category " + category + " added")
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(_handle)


def list_videos(url):
    """
    Create the list of playable videos in the Kodi interface.

    :param url: Url to video directory
    :type url: str
    """
    httpdata = search(url)
    raw_html_data = BeautifulSoup(httpdata, "html.parser").find_all("article", class_="penci-imgtype-landscape")
    # parser=HTMLParser()
    for (data) in raw_html_data:
        titledata = data.find("h2", class_="entry-title").find("a")
        title = titledata.text
        url = titledata["href"]
        plot = data.find("div", class_="entry-content").text
        thumb = data.find("a", class_="penci-link-post")["data-src"]
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'plot': plot,
                                    'mediatype': 'video'})
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=url)
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    next = re.search(r'<a class="next page-numbers" href="(\S*?)"', httpdata)
    if next:
        url = get_url(action='listing', url=next.group(1))
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, xbmcgui.ListItem(label='Ďalšie'), is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # get video link
    html = search(path)
    if html:
        videolink = BeautifulSoup(html, "html.parser").find("video")["src"]
        xbmc.log(videolink)
        play_item = xbmcgui.ListItem(path=videolink)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos
            list_videos(params['url'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
