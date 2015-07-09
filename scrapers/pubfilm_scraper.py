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
import xbmcaddon
import xbmc
from salts_lib import dom_parser
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES

BASE_URL = 'http://pubfilm.com'

class PubFilm_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'pubfilm'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        if 'views' in item and item['views']:
            label += ' (%s views)' % item['views']
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            
            views = None
            fragment = dom_parser.parse_dom(html, 'span', {'class': 'post-views'})
            if fragment:
                fragment = fragment[0]
                views = re.sub('[^\d]', '', fragment)
                
            iframe_items = set(dom_parser.parse_dom(html, 'iframe', ret='src'))
            link_items = set(dom_parser.parse_dom(html, 'a', {'target': 'EZWebPlayer'}, ret='href'))
            items = list(iframe_items | link_items)
            for item in items:
                links = self.__get_links(item)
                for link in links:
                    hoster = {'multi-part': False, 'url': link, 'class': self, 'quality': self._height_get_quality(links[link]), 'host': self._get_direct_hostname(link), 'rating': None, 'views': views, 'direct': True}
                    hosters.append(hoster)

        return hosters

    def __get_links(self, url):
        url = url.replace('&#038;', '&')
        html = self._http_get(url, cache_limit=.5)
        links = {}
        for match in re.finditer('file\s*:\s*"([^"]+)"\s*,\s*label\s*:\s*"([^"]+)p', html):
            links[match.group(1)] = match.group(2)
        
        for match in re.finditer('<source\s+src=\'([^\']+)[^>]*data-res="([^"]+)P', html):
            links[match.group(1)] = match.group(2)
        
        return links
            
        
    def get_url(self, video):
        return super(PubFilm_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/?s=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=0)
        results = []
        items = dom_parser.parse_dom(html, 'h3', {'class': 'post-box-title'})
        for item in items:
            match = re.search('href="([^"]+)"[^>]*>([^<]+)', item)
            if match:
                url, match_title_year = match.groups()
                match = re.search('(.*)\s+(\d{4})$', match_title_year)
                if match:
                    match_title, match_year = match.groups()
                else:
                    match_title = match_title_year
                    match_year = ''

                url = url.replace(self.base_url, '')
                if url == '/': continue
                
                if not year or not match_year or year == match_year:
                    result = {'url': url, 'title': match_title, 'year': match_year}
                    results.append(result)
        return results

    def _http_get(self, url, cache_limit=8):
        html = super(PubFilm_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, cache_limit=cache_limit)
        cookie = self._get_sucuri_cookie(html)
        if cookie:
            log_utils.log('Setting Pubfilm cookie: %s' % (cookie), xbmc.LOGDEBUG)
            html = super(PubFilm_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, cookies=cookie, cache_limit=0)
        return html
