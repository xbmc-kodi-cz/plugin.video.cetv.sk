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
LIVE_URL='http://213.81.153.221:8080/cetv'


FEEDS = OrderedDict([        
        ('Spravodajstvo','http://cetv.sk/category/archiv/spravodajstvo/'),
        ('Publicistika','http://cetv.sk/category/archiv/publicistika/'),
        ('Šport','http://cetv.sk/category/archiv/sport/'),
        ('Relácie','http://cetv.sk/category/archiv/relacie/')
        ])

def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s"%(_scriptname_,msg.__str__()), level)

def logN(msg):
    log(msg,level=xbmc.LOGNOTICE)

def fetchUrl(url, label):
    logN("fetchUrl " + url + ", label:" + label)
    httpdata = ''	
    req = urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0')
    resp = urllib2.urlopen(req)
    httpdata = resp.read()
    httpdata = unicode(httpdata,'utf-8')
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
        url = get_url(action='listing', url=FEEDS[category])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        logN("category " + category + " added")
    list_item=xbmcgui.ListItem('Live vysielanie')
    list_item.setInfo( type="Video", infoLabels={ "Title": 'Live vysielanie', "Plot": ''} )
    xbmcplugin.addDirectoryItem(_handle,LIVE_URL,list_item, False)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)

    
    xbmcplugin.endOfDirectory(_handle)

def list_videos(url):
    """
    Create the list of playable videos in the Kodi interface.

    :param url: Url to video directory
    :type url: str
    """
    httpdata = fetchUrl(url, "Loading categories...")
    parser=HTMLParser()
    for (data) in re.findall(r'<article class="penci-imgtype-landscape(.+?)<\/article>', httpdata, re.DOTALL):
        title=re.search(r'rel="bookmark">(.*?)<\/a><\/h2>',data)
        title = parser.unescape(title.group(1)) if title else ''
        url=re.search(r'<a href="(\S+?)" rel="bookmark"',data).group(1)
        plot=re.search(r'<div class="entry-content">(.*?)<\/div>',data).group(1)
        plot=parser.unescape(plot)
        thumb=re.search(r' data-src="(\S*?)">',data)
        thumb = thumb.group(1) if thumb else ''
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
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
		
    next=re.search(r'<a class="next page-numbers" href="(\S*?)"',httpdata)
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
    html = fetchUrl(path, "Loading video...")
    if html:
        videolink=re.search(r'"(http:\/\/\S+?\.mp4)"',html).group(1)
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

