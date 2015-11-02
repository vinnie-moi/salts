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
from salts_lib import kodi
from salts_lib import log_utils
from salts_lib import dom_parser
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import USER_AGENT

BASE_URL = 'https://mvsnap.com'

class Mvsnap_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'mvsnap'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            fragment = dom_parser.parse_dom(html, 'select', {'id': 'myDropdown'})
            if fragment:
                fragment = fragment[0]
                for match in re.finditer('<option\s+value="([^"]+)', fragment):
                    for item in match.group(1).split(','):
                        if '|' in item:
                            q_str, stream_url = item.split('|')
                            stream_url += '|User-Agent=%s' % (USER_AGENT)
                            host = self._get_direct_hostname(stream_url)
                            hoster = {'multi-part': False, 'host': host, 'class': self, 'quality': self._blog_get_quality(video, q_str, host), 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                            hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(Mvsnap_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/v1/api/search?query=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=.25)
        results = []
        if html:
            try:
                js_data = json.loads(html)
            except ValueError:
                log_utils.log('Invalid JSON returned: %s: %s' % (search_url, html), log_utils.LOGWARNING)
            else:
                if 'movies' in js_data:
                    for item in js_data['movies']:
                        try:
                            if item['type'] != 'movies':
                                continue
                            
                            match = re.search('(.*)(?:\s+\((\d{4})\))', item['long_title'])
                            if match:
                                match_title, match_year = match.groups()
                            else:
                                match_title = item['long_title']
                                match_year = ''
                            
                            if not year or not match_year or year == match_year:
                                result = {'title': match_title, 'url': '/movies/%s' % (item['slug']), 'year': match_year}
                                results.append(result)
                        except KeyError:
                            pass
        return results
