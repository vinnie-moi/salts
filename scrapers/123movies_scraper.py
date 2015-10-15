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
import xml.etree.ElementTree as ET
from salts_lib import log_utils
from salts_lib import kodi
from salts_lib import dom_parser
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH

BASE_URL = 'http://123movies.to'

class One23Movies_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return '123Movies'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            match = re.search('var\s+url_playlist\s*=\s*"([^"]+)', html)
            if match:
                playlist_url = match.group(1)
                for match in re.finditer('changeServer\(\s*(\d+)\s*,', html):
                    url = playlist_url + '/' + match.group(1)
                    xml = self._http_get(url, cache_limit=.5)
                    sources = self.__get_links_from_xml(xml, video)
                    for source in sources:
                        hoster = {'multi-part': False, 'host': self._get_direct_hostname(source), 'class': self, 'quality': sources[source], 'views': None, 'rating': None, 'url': source, 'direct': True}
                        hosters.append(hoster)
        return hosters

    def __get_links_from_xml(self, xml, video):
        root = ET.fromstring(xml)
        ns = {'jwplayer': 'http://rss.jwpcdn.com/'}
        sources = {}
        for item in root.findall('.//item'):
            title = item.find('title').text
            for source in item.findall('jwplayer:source', ns):
                stream_url = source.get('file')
                label = source.get('label')
                if self._get_direct_hostname(stream_url) == 'gvideo':
                    quality = self._gv_get_quality(stream_url)
                elif label:
                    quality = self._height_get_quality(label)
                else:
                    quality = self._blog_get_quality(video, title, '')
                sources[stream_url] = quality
                log_utils.log('Adding stream: %s Quality: %s' % (stream_url, quality), log_utils.LOGDEBUG)
        return sources
    
    def get_url(self, video):
        return super(One23Movies_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/movie/search/')
        search_url += urllib.quote_plus('%s' % (title))
        html = self._http_get(search_url, cache_limit=1)
        results = []
        for item in dom_parser.parse_dom(html, 'div', {'class': 'ml-item'}):
            match_title = dom_parser.parse_dom(item, 'span', {'class': 'mli-info'})
            match_url = re.search('class="jtip-bottom".*?href="([^"]+)', item, re.DOTALL)
            match_year = re.search('class="jt-info">(\d{4})<', item)
            is_episodes = dom_parser.parse_dom(item, 'span', {'class': 'mli-eps'})
            
            if match_title and match_url and not is_episodes:
                match_title = match_title[0]
                match_title = re.sub('</?h2>', '', match_title)
                match_title = re.sub('\s+\d{4}$', '', match_title)
                url = match_url.group(1)
                match_year = match_year.group(1) if match_year else ''

                if not year or not match_year or year == match_year:
                    result = {'title': match_title, 'year': match_year, 'url': url.replace(self.base_url, '')}
                    results.append(result)

        return results

    def _http_get(self, url, data=None, cache_limit=8):
        return super(One23Movies_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)
