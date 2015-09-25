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
import json
from salts_lib import kodi
from salts_lib import dom_parser
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

BASE_URL = 'http://movietv.to'
LINK_URL = '/series/getLink?id=%s&s=%s&e=%s'

class MovieTV_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'movietv.to'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s ' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=1)
            if video.video_type == VIDEO_TYPES.MOVIE:
                pattern = '<source\s+src="([^"]+)'
                match = re.search(pattern, html)
                if match:
                    html = '{"url":"%s"}' % (match.group(1))
                else:
                    return hosters
                quality = QUALITIES.HD720
            else:
                quality = QUALITIES.HIGH

            try:
                js_data = json.loads(html)
                if js_data['url']:
                    stream_url = js_data['url'] + '|referer=%s' % (url)
                    hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'url': stream_url, 'quality': quality, 'views': None, 'rating': None, 'direct': True}
                    hosters.append(hoster)
            except ValueError:
                pass

        return hosters

    def get_url(self, video):
        return super(MovieTV_Scraper, self)._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        episode_pattern = 'playSeries\((\d+),%s,%s\)' % (video.season, video.episode)
        title_pattern = ''
        airdate_pattern = ''
        result = super(MovieTV_Scraper, self)._default_get_episode_url(show_url, video, episode_pattern, title_pattern, airdate_pattern)
        return LINK_URL % (result, video.season, video.episode)

    def search(self, video_type, title, year):
        results = []
        url = urlparse.urljoin(self.base_url, '/search?q=')
        url += urllib.quote_plus(title)
        html = self._http_get(url, cache_limit=.25)
        if video_type == VIDEO_TYPES.MOVIE:
            url_frag = '/movies/'
        else:
            url_frag = '/series/'

        for item in dom_parser.parse_dom(html, 'div', {'class': '[^"]*movie-grid[^"]*'}):
            match = re.search('href="([^"]+).*?class="movie-grid-title">\s*([^<]+).*?movie-grid-year">(\d+)', item, re.DOTALL)
            if match:
                link, match_title, match_year = match.groups()
                if url_frag in link and (not year or not match_year or int(year) == int(match_year)):
                    result = {'url': link, 'title': match_title, 'year': match_year}
                    results.append(result)

        return results

    def _http_get(self, url, data=None, headers=None, allow_redirect=True, cache_limit=8):
        return super(MovieTV_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, headers=headers, allow_redirect=allow_redirect, cache_limit=cache_limit)
