"""
    SALTS XBMC Addon
    Copyright (C) 2015 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import xbmcaddon
import xbmcplugin
import xbmcgui
import urllib
import urlparse
import sys

addon = xbmcaddon.Addon()
get_setting = addon.getSetting
show_settings = addon.openSettings

def set_setting(id, value):
    addon.setSetting(id, value)

def get_path():
    return addon.getAddonInfo('path')

def get_version():
    return addon.getAddonInfo('version')

def get_id():
    return addon.getAddonInfo('id')

def get_name():
    return addon.getAddonInfo('name')

def get_plugin_url(queries):
    return sys.argv[0] + '?' + urllib.urlencode(queries)

def end_of_directory(cache_to_disc=True):
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cache_to_disc)

def add_item(queries, label, thumb='', fanart='', is_folder=None, is_playable=None, total_items=0):
    if is_folder is None:
        is_folder = False if is_playable else True

    if is_playable is None:
        playable = 'false' if is_folder else 'true'
    else:
        playable = 'true' if is_playable else 'false'

    url = get_plugin_url(queries)
    list_item = xbmcgui.ListItem(label, iconImage=thumb, thumbnailImage=thumb)
    list_item.setProperty('fanart_image', fanart)
    list_item.setInfo('video', {'title': label})
    list_item.setProperty('isPlayable', playable)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isFolder=is_folder, totalItems=total_items)

def parse_query(query):
    q = {'mode': 'main'}
    if query.startswith('?'): query = query[1:]
    queries = urlparse.parse_qs(query)
    for key in queries:
        if len(queries[key]) == 1:
            q[key] = queries[key][0]
        else:
            q[key] = queries[key]
    return q
