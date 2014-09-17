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
import re
import urllib
import urlparse
import xbmcaddon
import xbmc
from salts_lib.db_utils import DB_Connection
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

QUALITY_MAP = {'DVD': QUALITIES.HIGH, 'TS': QUALITIES.MEDIUM, 'CAM': QUALITIES.LOW}
BASE_URL = 'http://www.alluc.to'

class PW_Scraper(scraper.Scraper):
    base_url=BASE_URL
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout=timeout
        self.db_connection = DB_Connection()
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))
   
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])
    
    @classmethod
    def get_name(cls):
        return 'Alluc.to'
    
    def resolve_link(self, link):
        return link
    
    def format_source_label(self, item):
        label='[%s] %s (%s views) (%s/100) ' % (item['quality'], item['host'], item['views'], item['rating'])
        if item['verified']: label = '[COLOR yellow]%s[/COLOR]' % (label)
        return label
    
    def get_sources(self, video):
        source_url=self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            
            # extract direct links section
            match = re.search('Direct Links.*', html, re.DOTALL)
            if match:
                container = match.group()
                # extract each group
                for match in re.finditer('class="grouphosterlabel">(.*?)\s+\(\d+\)(.*?)class="grouphosterlabel">', container, re.DOTALL):
                    host, group = match.groups()
                    print host, group
            # extract links in each group

        return hosters

    def get_url(self, video):
        return super(PW_Scraper, self)._default_get_url(video)
    
    def search(self, video_type, title, year):
        if video_type == VIDEO_TYPES.MOVIE:
            search_url = urlparse.urljoin(self.base_url, '/movies.html')
        else:
            search_url = urlparse.urljoin(self.base_url, '/tv-shows.html')
        search_url+='?sword=%s' % (urllib.unquote_plus(title)) # only to force url cache to work
        data = {'mode': 'search', 'sword': title}
            
        results=[]
        html = self._http_get(search_url, data, cache_limit=.25)
        pattern = r'class="newlinks" href="([^"]+)" title="watch\s+(.*?)\s*(?:\((\d{4})\))?\s+online"'
        for match in re.finditer(pattern, html):
            url, match_title, match_year = match.groups('')
            if not year or not match_year or year == match_year:
                match_title = match_title.replace(r"\'","'")
                if not url.startswith('/'): url = '/' + url
                results.append({'url': url, 'title': match_title, 'year': match_year})
        return results
    
    def _get_episode_url(self, show_url, season, episode, ep_title):
        season='%02d' % (int(season))
        episode='%02d' % (int(episode))
        episode_pattern = 'href="([^"]+)" title="watch[^"]+Season\s+%s\s+Episode\s+%s\s+online' % (season, episode)
        return super(PW_Scraper, self)._default_get_episode_url(show_url, season, episode, ep_title, episode_pattern)
        
    def _http_get(self, url, data=None, cache_limit=8):
        return super(PW_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)