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
import urllib
import urlparse
import re
import json
from salts_lib import log_utils
from salts_lib import kodi
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import XHR
from salts_lib.constants import QUALITIES

BASE_URL = 'http://torba.se'
SEARCH_URL = '/api/movies/list.json?genres=All+genres&limit=40&order=recent&q=%s&year=All+years'
PLAYER_URL = '/api/movies/player.json?slug=%s'

class TorbaSe_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'torba.se'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            slug = re.sub('^/v/', '', source_url)
            source_url = PLAYER_URL % (slug)
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            html = html.replace('\\"', '"')
            match = re.search('<iframe[^>]+src="([^"]+)', html)
            if match:
                st_url = match.group(1)
                html = self._http_get(st_url, cache_limit=.5)
                match = re.search('{\s*file\s*:\s*"([^"]+)', html)
                if match:
                    pl_url = urlparse.urljoin(st_url, match.group(1))
                    playlist = self._http_get(pl_url, cache_limit=.5)
                    sources = self.__get_streams_from_m3u8(playlist.split('\n'))
                    for source in sources:
                        stream_url = urlparse.urljoin(st_url, source)
                        hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': sources[source], 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                        hosters.append(hoster)
                
        return hosters

    def __get_streams_from_m3u8(self, playlist):
        sources = {}
        quality = QUALITIES.HIGH
        for line in playlist:
            if line.startswith('#EXT-X-STREAM-INF'):
                match = re.search('NAME="(\d+)p', line)
                if match:
                    quality = self._height_get_quality(match.group(1))
            elif line.endswith('m3u8'):
                sources[line] = quality
                
        return sources
        
    def get_url(self, video):
        return super(TorbaSe_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, SEARCH_URL)
        search_url = search_url % (urllib.quote_plus(title))
        html = self._http_get(search_url, headers=XHR, cache_limit=1)
        results = []
        if html:
            try:
                js_result = json.loads(html)
            except ValueError:
                log_utils.log('Invalid JSON returned: %s: %s' % (search_url, html), log_utils.LOGWARNING)
            else:
                if 'result' in js_result:
                    for item in js_result['result']:
                        match_title = item['title']
                        match_year = str(item['year']) if 'year' in item else ''
    
                        if not year or not match_year or year == match_year:
                            result = {'title': match_title, 'year': match_year, 'url': '/v/' + item['slug']}
                            results.append(result)

        return results

    def _http_get(self, url, data=None, headers=None, cache_limit=8):
        return super(TorbaSe_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, headers=headers, cache_limit=cache_limit)
