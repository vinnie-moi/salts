"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

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
import scraper
import xbmcaddon
import xbmc
import os
import base64
from salts_lib import pyaes
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES

PY_URL = ''
PB_KEY = base64.decodestring('YV9sb25nX2Flc19rZXlfZm9yX3NodXNoX3NjcmFwZXI=')
IV = '\0' * 16

class Shush_Proxy(scraper.Scraper):
    
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.__update_scraper_py()
        import shush_scraper
        self.__scraper = shush_scraper.Shush_Scraper(timeout)
   
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])
    
    @classmethod
    def get_name(cls):
        return 'Shush.se'
    
    def resolve_link(self, link):
        return self.__scraper.resolve_link(link)
    
    def format_source_label(self, item):
        return self.__scraper.format_source_label(item)
    
    def get_sources(self, video):
        return self.__scraper.get_sources(video)
            
    def get_url(self, video):
        return self.__scraper.get_url(video)
    
    def search(self, video_type, title, year):
        return self.__scraper.search(video_type, title, year)
    
    def _get_episode_url(self, show_url, video):
        return self.__scraper._get_episode_url(show_url, video)

    def _http_get(self, url, cache_limit=8):
        return super(Shush_Proxy, self)._cached_http_get(url, '', self.timeout, cache_limit=cache_limit)
    
    def __update_scraper_py(self):
        path = xbmcaddon.Addon().getAddonInfo('path')
        py_path = os.path.join(path, 'scrapers', 'shush_scraper.py')
        cipher_text = self._http_get(PY_URL, cache_limit=4)
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(PB_KEY, IV))
        new_py = decrypter.feed(cipher_text)
        new_py += decrypter.feed()
        
        old_py = ''
        if os.path.exists(py_path):
            with open(py_path, 'r') as f:
                old_py = f.read()
        
        log_utils.log('shush path: %s, new_py: %s, match: %s' % (py_path, bool(new_py), new_py == old_py), xbmc.LOGDEBUG)
        if new_py and old_py != new_py:
            with open(py_path, 'w') as f:
                f.write(new_py)
