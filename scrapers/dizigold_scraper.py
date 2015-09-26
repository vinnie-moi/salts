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
import urlparse
import json
from salts_lib import dom_parser
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import USER_AGENT
from salts_lib import kodi

BASE_URL = 'http://www.dizigold.net'
AJAX_URL = '/sistem/ajax.php'
XHR = {'X-Requested-With': 'XMLHttpRequest'}

class Dizigold_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))
        self.ajax_url = urlparse.urljoin(self.base_url, AJAX_URL)

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'Dizigold'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s ' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            page_url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(page_url, cache_limit=.25)
            match = re.search('var\s+view_id\s*=\s*"([^"]+)', html)
            if match:
                view_data = {'id': match.group(1), 'tip': 'view'}
                html = self._http_get(self.ajax_url, data=view_data, headers=XHR, cache_limit=0)
                html = re.sub(r'\\n|\\t|\\', '', html)
                match = re.search('var\s+sources\s*=\s*(\[.*?\])', html)
                if match:
                    try:
                        js_data = json.loads(match.group(1))
                    except ValueError:
                        log_utils.log('Invalid JSON returned: %s: %s' % (view_data, html), log_utils.LOGWARNING)
                    else:
                        for source in js_data:
                            stream_url = source['file'] + '|User-Agent=%s' % (USER_AGENT)
                            if self._get_direct_hostname(stream_url) == 'gvideo':
                                quality = self._gv_get_quality(stream_url)
                            else:
                                quality = self._height_get_quality(source['label'])
                        
                            hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                            hosters.append(hoster)
    
        return hosters

    def get_url(self, video):
        return super(Dizigold_Scraper, self)._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        show_url = urlparse.urljoin(self.base_url, show_url)
        html = self._http_get(show_url, cache_limit=8)
        dizi_id = dom_parser.parse_dom(html, 'div', {'id': 'icerikid'}, 'value')
        if dizi_id:
            season_data = {'sezon_id': video.season, 'dizi_id': dizi_id[0], 'tip': 'sezon'}
            html = self._http_get(self.ajax_url, data=season_data, headers=XHR, cache_limit=0)
            html = re.sub(r'\\n|\\t|\\', '', html)
            force_title = self._force_title(video)

            if not force_title:
                episode_pattern = 'href="([^"]+/%s-sezon/%s-bolum/?)' % (video.season, video.episode)
                match = re.search(episode_pattern, html, re.DOTALL)
                if match:
                    return match.group(1).replace(self.base_url, '')
            
            if (force_title or kodi.get_setting('title-fallback') == 'true') and video.ep_title:
                norm_title = self._normalize_title(video.ep_title)
                for item in dom_parser.parse_dom(html, 'div', {'class': '[^"]*playlist-content[^"]*'}):
                    match = re.search('href="([^"]+)', item)
                    ep_title = dom_parser.parse_dom(item, 'p', {'class': 'realcuf'})
                    if match and ep_title:
                        if norm_title == self._normalize_title(ep_title[0]):
                            return match.group(1).replace(self.base_url, '')

    def search(self, video_type, title, year):
        html = self._http_get(self.base_url, cache_limit=8)
        results = []
        fragment = dom_parser.parse_dom(html, 'div', {'class': 'dizis'})
        norm_title = self._normalize_title(title)
        if fragment:
            for match in re.finditer('href="([^"]+)">([^<]+)', fragment[0]):
                url, match_title = match.groups()
                if norm_title in self._normalize_title(match_title):
                    result = {'url': url.replace(self.base_url, ''), 'title': match_title, 'year': ''}
                    results.append(result)

        return results

    def _http_get(self, url, data=None, headers=None, cache_limit=8):
        return super(Dizigold_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, headers=headers, cache_limit=cache_limit)
