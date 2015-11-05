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
from salts_lib import dom_parser
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import USER_AGENT
from salts_lib.constants import QUALITIES
from salts_lib.constants import XHR
from salts_lib import kodi

BASE_URL = 'http://www.dizibox.com'
OK_META_URL = 'http://ok.ru/dk?cmd=videoPlayerMetadata&mid=%s'
ALTERNATIVES = ['DBX', '1080P', '1080p', 'İngilizce', 'Altyazısız']
OK_QUALITIES = {'MOBILE': QUALITIES.LOW, 'LOWEST': QUALITIES.MEDIUM, 'LOW': QUALITIES.MEDIUM, 'SD': QUALITIES.HIGH, 'HD': QUALITIES.HD720}

class Dizibox_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'Dizibox'

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
            html = self._http_get(page_url, cache_limit=.5)
            hosters += self.__get_links(html, page_url)
            if 'altyazi.png' in html:
                for hoster in hosters:
                    hoster['subs'] = True

            for match in re.finditer("<option\s+value='([^']+)[^>]+>([^<]+)", html):
                if match.group(2) in ALTERNATIVES:
                    html = self._http_get(match.group(1), cache_limit=.5)
                    hosters += self.__get_links(html, page_url)
                    if match.group(2) != 'Altyazısız':
                        for hoster in hosters:
                            hoster['subs'] = True
        
        return hosters

    def __get_links(self, html, page_url):
        sources = []
        seen_urls = {}
        fragment = dom_parser.parse_dom(html, 'span', {'class': 'object-wrapper'})
        iframe_src = dom_parser.parse_dom(fragment[0], 'iframe', ret='src')
        iframe_html = self._http_get(iframe_src[0], cache_limit=.10)
        match = re.search('src="([^"]*ok.ru/videoembed/[^"]+)', iframe_html)
        if match:
            sources = self.__get_ok_links(match.group(1))
        else:
            for match in re.finditer('"?file"?\s*:\s*"([^"]+)"\s*,\s*"?label"?\s*:\s*"(\d+)p?"', iframe_html):
                stream_url, height = match.groups()
                stream_url = stream_url.replace('\\&', '&')
                if stream_url in seen_urls: continue
                seen_urls[stream_url] = True
                host = self._get_direct_hostname(stream_url)
                if host == 'gvideo':
                    quality = self._gv_get_quality(stream_url)
                else:
                    quality = self._height_get_quality(height)
                    stream_url += '|User-Agent=%s&Referer=%s' % (USER_AGENT, urllib.quote(page_url))
                hoster = {'multi-part': False, 'host': host, 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                sources.append(hoster)
        return sources
    
    def __get_ok_links(self, embed_url):
        sources = []
        match = re.search('videoembed/(.*)', embed_url)
        if match:
            meta_url = OK_META_URL % (match.group(1))
            headers = XHR
            headers['Referer'] = embed_url
            html = self._http_get(meta_url, headers=headers, cache_limit=.5)
            if html:
                try:
                    js_result = json.loads(html)
                except ValueError:
                    log_utils.log('Invalid JSON returned: %s: %s' % (meta_url, html), log_utils.LOGWARNING)
                else:
                    if 'videos' in js_result:
                        for video in js_result['videos']:
                            stream_url = video['url'] + '|User-Agent=%s&Referer=%s' % (USER_AGENT, urllib.quote(embed_url))
                            quality = OK_QUALITIES.get(video['name'].upper(), QUALITIES.HIGH)
                            hoster = {'multi-part': False, 'host': self._get_direct_hostname(video['url']), 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                            sources.append(hoster)
        return sources
    
    def get_url(self, video):
        return super(Dizibox_Scraper, self)._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        show_url = urlparse.urljoin(self.base_url, show_url)
        html = self._http_get(show_url, cache_limit=24)
        season_pattern = 'href=["\']([^"\']+)[^>]*>%s\.?\s+Sezon<' % (video.season)
        match = re.search(season_pattern, html)
        if match:
            episode_pattern = 'href=["\']([^"\']+-%s-sezon-%s-[^"\']*bolum[^"\']*)' % (video.season, video.episode)
            return super(Dizibox_Scraper, self)._default_get_episode_url(match.group(1), video, episode_pattern)

    def search(self, video_type, title, year):
        html = self._http_get(self.base_url, cache_limit=8)
        results = []
        norm_title = self._normalize_title(title)
        for fragment in dom_parser.parse_dom(html, 'div', {'class': 'category-list-wrapper'}):
            for match in re.finditer('href=["\']([^"\']+)["\']>([^<]+)', fragment):
                url, match_title = match.groups()
                if norm_title in self._normalize_title(match_title):
                    result = {'url': self._pathify_url(url), 'title': match_title, 'year': ''}
                    results.append(result)

        return results
