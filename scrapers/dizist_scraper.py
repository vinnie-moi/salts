# -*- coding: utf-8 -*-
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
import urllib
import json
from salts_lib import log_utils
from salts_lib import dom_parser
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import USER_AGENT
from salts_lib.constants import XHR
from salts_lib import kodi

BASE_URL = 'http://dizist.net'
SEASON_URL = '/posts/dizigonder.php?action=sezongets'
VK_URL = '/vkjson.php?oid=%s&video_id=%s&embed_hash=%s'
OK_URL = '/okrujson.php?v=%s'

class Dizist_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'Dizist'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        if 'subs' in item:
            label += ' (Turkish subtitles)'
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            page_url = urlparse.urljoin(self.base_url, source_url)
            hosters += self.__get_links(page_url)
            
#             html = self._http_get(page_url, cache_limit=.5)
#             fragment = dom_parser.parse_dom(html, 'div', {'class': 'topboxs'})
#             if fragment:
#                 for match in re.finditer("href='([^']+)", fragment[0]):
#                     if match.group(1) != source_url:
#                         page_url = urlparse.urljoin(self.base_url, match.group(1))
#                         hosters += self.__get_links(page_url)
         
        return hosters

    def __get_links(self, url):
        sources = {}
        hosters = []
        html = self._http_get(url, cache_limit=.5)
        for iframe_url in dom_parser.parse_dom(html, 'iframe', ret='src'):
            if 'okru' in iframe_url:
                match = re.search("v=([^&]+)", iframe_url)
                if match:
                    source_url = OK_URL % (match.group(1))
                    source_url = urlparse.urljoin(self.base_url, source_url)
                    html = self._http_get(source_url, headers=XHR, cache_limit=.5)
                    sources = self.__parse_format(html)
            elif 'video_ext' in iframe_url:
                match = re.search('video_ext\.php\?oid=([^&]+)&id=([^&]+)&hash=([^&]+)', iframe_url)
                if match:
                    oid, video_id, embed_hash = match.groups()
                    source_url = VK_URL % (oid, video_id, embed_hash)
                    source_url = urlparse.urljoin(self.base_url, source_url)
                    html = self._http_get(source_url, headers=XHR, cache_limit=.5)
                    sources = self.__parse_format2(html)
        
        for source in sources:
            stream_url = source + '|User-Agent=%s&Referer=%s' % (USER_AGENT, urllib.quote(url))
            hoster = {'multi-part': False, 'host': self._get_direct_hostname(source), 'class': self, 'quality': sources[source], 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
            hosters.append(hoster)
        return hosters
    
    def __parse_format(self, html):
        sources = {}
        if html:
            try:
                js_result = json.loads(html)
            except ValueError:
                log_utils.log('Invalid JSON returned: %s: %s' % (html), log_utils.LOGWARNING)
            else:
                for item in js_result:
                    if re.match('\d+p', item):
                        sources[js_result[item]] = self._height_get_quality(item)
        return sources
    
    def __parse_format2(self, html):
        sources = {}
        if html:
            try:
                js_result = json.loads(html)
            except ValueError:
                log_utils.log('Invalid JSON returned: %s: %s' % (html), log_utils.LOGWARNING)
            else:
                if 'response' in js_result:
                    for item in js_result['response']:
                        match = re.match('url(\d+)', item)
                        if match:
                            quality = self._height_get_quality(match.group(1))
                            sources[js_result['response'][item]] = quality
        return sources
    
    def get_url(self, video):
        return super(Dizist_Scraper, self)._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        show_url = urlparse.urljoin(self.base_url, show_url)
        html = self._http_get(show_url, cache_limit=24)
        match = re.search('id="sezon_%s"' % (video.season), html)
        if match:
            match = re.search('<div\s+id="icerikid"\s+value="([^"]+)', html)
            if match:
                season_url = urlparse.urljoin(self.base_url, SEASON_URL)
                data = {'sezon_id': video.season, 'dizi_id': match.group(1), 'tip': 'dizi', 'bolumid': ''}
                episode_pattern = 'href=["\']([^"\']+-%s-sezon-%s-[^"\']*bolum[^"\']*)' % (video.season, video.episode)
                title_pattern = 'href="(/izle/[^"]+).*?<p[^>]*>([^<]+)'
                return super(Dizist_Scraper, self)._default_get_episode_url(season_url, video, episode_pattern, title_pattern, data=data, headers=XHR)

    def search(self, video_type, title, year):
        html = self._http_get(self.base_url, cache_limit=8)
        results = []
        norm_title = self._normalize_title(title)
        for fragment in dom_parser.parse_dom(html, 'div', {'class': 'dizis'}):
            for match in re.finditer('href=["\']([^"\']+)["\']>([^<]+)', fragment):
                url, match_title = match.groups()
                if norm_title in self._normalize_title(match_title):
                    result = {'url': self._pathify_url(url), 'title': match_title, 'year': ''}
                    results.append(result)

        return results
