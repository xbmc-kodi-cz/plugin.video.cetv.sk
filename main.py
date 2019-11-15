# -*- coding: utf-8 -*-
# Module: default
# Author: rywko
# Created on: 15.11.2019
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys, os
from collections import OrderedDict
from urllib import urlencode
import urllib2
from urlparse import parse_qsl
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import re
from HTMLParser import HTMLParser


# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
_addon_ = xbmcaddon.Addon('plugin.video.cetv.sk')
_scriptname_ = _addon_.getAddonInfo('name')
home = _addon_.getAddonInfo('path')
__baseurl__ = 'http://cetv.sk'


FEEDS = OrderedDict([        
        ('Spravodajstvo','http://cetv.sk/index.php/spravodajstvo'),
        ('Publicistika','http://cetv.sk/index.php/publicistika'),
        ('Šport','http://cetv.sk/index.php/sport'),
        ('Relácie','http://cetv.sk/index.php/archiv/relacie')
        ])

def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s"%(_scriptname_,msg.__str__()), level)

def logDbg(msg):
    log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
    log(msg,level=xbmc.LOGERROR)

def fetchUrl(url, label):
    logErr("fetchUrl " + url + ", label:" + label)
    httpdata = ''	
    req = urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0')
    resp = urllib2.urlopen(req)
    httpdata = resp.read()
    resp.close()
    return httpdata

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

    for category in FEEDS.iterkeys():
        list_item = xbmcgui.ListItem(label=category)
      
        url = get_url(action='listing', category=category)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        logErr("category " + category + " added")
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    
    xbmcplugin.endOfDirectory(_handle)

def list_videos(category):
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    url=FEEDS[category]
    httpdata = fetchUrl(url, "Loading categories...")
    parser=HTMLParser()
    for (url, title, thumb) in re.findall(r'<a href="(\S+?)" title="(.*?)">\s*<img src="(\S+?)"', httpdata):
        title=unicode(title, encoding="utf-8", errors="ignore")
        title=parser.unescape(title).encode('utf-8')
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=title)
    
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': title,
                                    'plot': '',
                                    'mediatype': 'video'})
                                    
        list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})

        list_item.setProperty('IsPlayable', 'true')
        
        url='plugin://plugin.video.cetv.sk/?action=play&video=' + __baseurl__+ url
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False

        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # get video link
    html = fetchUrl(path, "Loading video...")
    print html
    if html:
        videolink=re.findall(r'source:\'(\S+?)\',',html)[0]
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
            # Display the list of videos in a provided category.
            list_videos(params['category'])
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
