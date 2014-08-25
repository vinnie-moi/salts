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
import urllib
import urllib2
import urlparse
import re
from salts_lib.db_utils import DB_Connection
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import USER_AGENT

db_connection = DB_Connection()

class UFlix_Scraper(scraper.Scraper):
    def __init__(self):
        self.base_url = 'http://uflix.org'
    
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])
    
    def get_name(self):
        return 'UFlix.org'
    
    def resolve_link(self, link):
        return link
    
    def format_source_label(self, item):
        return ''
    
    def get_sources(self, video_type, title, year, season='', episode=''):
        return []

    def get_url(self, video_type, title, year, season='', episode=''):
        result=db_connection.get_related_url(video_type, title, year, self.get_name(), season, episode)
        if result:
            return result[0][0]
    
    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/index.php?menu=search&query=')
        search_url += urllib.quote_plus(title)
        html = self.__http_get(search_url, cache_limit=.25)
        results=[]
        
        # filter the html down to only tvshow or movie results
        if video_type in [VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE]:
            pattern='<div id="grid2".*'
        else:
            pattern='<div id="grid".*<div id="grid2"'
        match = re.search(pattern, html, re.DOTALL)
        try:
            fragment = match.group(0)
            pattern = '<a title="Watch (.*?) Online For FREE".*href="(.*?)".*\((\d{4})\)</a>'
            for match in re.finditer(pattern, fragment):
                result={}
                title, url, year = match.groups()
                result['title']=title
                result['url']=url.replace(self.base_url,'')
                result['year']=year
                results.append(result)
        except Exception as e:
            log_utils.log('Failure during %s search: |%s|%s|%s| (%s)' % (self.get_name(), video_type, title, year, str(e)), xbmc.LOGWARNING)
        
        return results
        
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
        