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
import xbmc
import urllib2
import re
from salts_lib.db_utils import DB_Connection
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import USER_AGENT

db_connection = DB_Connection()

class WS_Scraper(scraper.Scraper):
    def __init__(self):
        self.base_url = 'http://watchseries.sx'
    
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE])
    
    def get_name(self):
        return 'WatchSeries'
    
    def resolve_link(self, link):
        return link
    
    def format_source_label(self, item):
        return ''
    
    def get_sources(self, video_type, title, year, season='', episode=''):
        url = self.base_url + '/episode/breaking_bad_s5_e16.html'
        html = self.__http_get(url, cache_limit=.5)
        try:
            sources=[]
            match = re.search('English Links -.*?</tbody>\s*</table>', html, re.DOTALL)
            fragment = match.group(0)
            pattern = 'href\s*=\s*"([^"]*)"\s+class\s*=\s*"buttonlink"\s+title\s*=([^\s]*).*?<span class="percent"[^>]+>\s+(\d+)%\s+</span>'
            for match in re.finditer(pattern, fragment, re.DOTALL):
                source = {'multi-part': False}
                url, host, rating = match.groups()
                source['url']=url
                source['host']=host
                source['rating']=rating
                sources.append(source)
        except Exception as e:
            log_utils.log('Failure During %s get sources: %s' % (self.get_name(), str(e)))
            
        return sources

    def get_url(self, video_type, title, year, season='', episode=''):
        result=db_connection.get_related_url(video_type, title, year, self.get_name(), season, episode)
        if result:
            return result[0][0]
    
    def search(self, video_type, title, year):
        raise NotImplementedError
    
    def __http_get(self, url, cache_limit=8):
        log_utils.log('Getting Url: %s' % (url))
        db_connection=DB_Connection()
        html = db_connection.get_cached_url(url, cache_limit)
        if html:
            log_utils.log('Returning cached result for: %s' % (url), xbmc.LOGDEBUG)
            return html
        
        request = urllib2.Request(url)
        request.add_header('User-Agent', USER_AGENT)
        request.add_unredirected_header('Host', request.get_host())
        request.add_unredirected_header('Referer', self.base_url)
        response = urllib2.urlopen(request, timeout=10)
        html=response.read()
        db_connection.cache_url(url, html)
        return html
        