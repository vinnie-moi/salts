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
import xbmcaddon
import json
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.db_utils import DB_Connection
from salts_lib.constants import QUALITIES
from salts_lib.constants import Q_ORDER

Q_LIST = [item[0] for item in sorted(Q_ORDER.items(), key=lambda x:x[1])]


BASE_URL = 'http://www.alluc.com'
SEARCH_URL = '/api/search/%s/?apikey=%s&query=%s&count=100&from=0&getmeta=0'
SEARCH_TYPES = ['stream', 'download']
API_KEY = '02216ecc1bf4bcc83a1ee6c72a5f0eda'
QUALITY_MAP = {
               QUALITIES.LOW: ['DVDSCR', 'CAMRIP', 'HDCAM'],
               QUALITIES.MEDIUM: [],
               QUALITIES.HIGH: ['BDRIP', 'BRRIP', 'HDRIP'],
               QUALITIES.HD: ['720P', '1080P']}

class Alluc_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.db_connection = DB_Connection()
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'alluc.com'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        hosters = []
        seen_urls = set()
        source_url = self.get_url(video)
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            for search_type in SEARCH_TYPES:
                url = self.__translate_search(url, search_type)
                html = self._http_get(url, cache_limit=.5)
                if html:
                    js_result = json.loads(html)
                    if js_result['status'] == 'success':
                        for result in js_result['result']:
                            if len(result['hosterurls']) > 1: continue
                            if result['extension'] == 'rar': continue
                            
                            stream_url = result['hosterurls'][0]['url']
                            if stream_url not in seen_urls:
                                host = urlparse.urlsplit(stream_url).hostname.lower()
                                quality = self._get_quality(video, host, self._get_title_quality(result['title']))
                                hoster = {'multi-part': False, 'class': self, 'views': None, 'url': stream_url, 'rating': None, 'host': host, 'quality': quality, 'direct': False}
                                hosters.append(hoster)
                                seen_urls.add(stream_url)

        return hosters

    def _get_title_quality(self, title):
        post_quality = QUALITIES.HIGH
        title = title.upper()
        for key in Q_LIST:
            if any(q in title for q in QUALITY_MAP[key]):
                post_quality = key

        #log_utils.log('Setting |%s| to |%s|' % (title, post_quality), xbmc.LOGDEBUG)
        return post_quality
    
    def get_url(self, video):
        url = None
        result = self.db_connection.get_related_url(video.video_type, video.title, video.year, self.get_name(), video.season, video.episode)
        if result:
            url = result[0][0]
            log_utils.log('Got local related url: |%s|%s|%s|%s|%s|' % (video.video_type, video.title, video.year, self.get_name(), url))
        else:
            if video.video_type == VIDEO_TYPES.MOVIE:
                query = urllib.quote_plus('%s %s' % (video.title, video.year))
            else:
                query = urllib.quote_plus('%s S%02dE%02d' % (video.title, int(video.season), int(video.episode)))
            url = '/search?query=%s' % (query)
            self.db_connection.set_related_url(video.video_type, video.title, video.year, self.get_name(), url)
        return url

    def search(self, video_type, title, year):
        return []

    def _http_get(self, url, cache_limit=8):
        return super(Alluc_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, cache_limit=cache_limit)

    def __translate_search(self, url, search_type):
        query = urlparse.parse_qs(urlparse.urlparse(url).query)
        return urlparse.urljoin(self.base_url, SEARCH_URL % (search_type, API_KEY, urllib.quote_plus(query['query'][0])))
