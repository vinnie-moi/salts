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
import urlparse
import xbmcaddon
from salts_lib import dom_parser
from salts_lib.constants import VIDEO_TYPES

BASE_URL = 'http://tubemotion.com'
FORM_DATA = '''--X-X-X\r
Content-Disposition: form-data; name="search"\r
\r
%s\r
--X-X-X\r
Content-Disposition: form-data; name="category"\r
\r
0\r
--X-X-X\r
Content-Disposition: form-data; name="submit"\r
\r
\r
--X-X-X\r
Content-Disposition: form-data; name="submit"\r
\r
Search\r
X-X-X--\r
'''

class TubeMotion_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'tubemotion'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            fragment = dom_parser.parse_dom(html, 'div', {'class': 'main_content'})
            if fragment:
                lines = fragment[0].split('\n')
                q_str = 'HDRIP'
                for line in lines:
                    if line.startswith('<a'):
                        match = re.search('href="([^"]+)', line)
                        if match:
                            stream_url = match.group(1)
                            host = urlparse.urlparse(stream_url).hostname
                            hoster = {'multi-part': False, 'host': host, 'class': self, 'quality': self._blog_get_quality(video, q_str, host), 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                            hosters.append(hoster)
                    elif not line.startswith('http://'):
                        q_str = line

        return hosters

    def get_url(self, video):
        return super(TubeMotion_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/search/')
        search_url += '?%s' % (urllib.quote_plus(title))
        html = self._http_get(search_url, multipart_data=FORM_DATA % (title), cache_limit=.25)
        results = []
        elements = dom_parser.parse_dom(html, 'div', {'class': 'box'})
        for element in elements:
            match = re.search('href="([^"]+).*?alt=\'([^\']+)', element, re.DOTALL)
            if match:
                url, match_title_year = match.groups()
                match = re.search('(.*?)(?:\s+\(?(\d{4})\)?)', match_title_year)
                if match:
                    match_title, match_year = match.groups()
                else:
                    match_title = match_title_year
                    match_year = ''
                
                if not year or not match_year or year == match_year:
                    result = {'title': match_title, 'year': match_year, 'url': urlparse.urlparse(url).path}
                    results.append(result)
        return results

    def _http_get(self, url, data=None, multipart_data=None, headers=None, cache_limit=8):
        return super(TubeMotion_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, multipart_data=multipart_data, headers=headers, cache_limit=cache_limit)

