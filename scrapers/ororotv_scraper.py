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
from salts_lib import kodi
import xbmc
from salts_lib import log_utils
from salts_lib.trans_utils import i18n
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES
from salts_lib.constants import USER_AGENT

BASE_URL = 'http://ororo.tv'
CATEGORIES = {VIDEO_TYPES.TVSHOW: '2,3', VIDEO_TYPES.MOVIE: '1,3,4'}

class OroroTV_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))
        self.username = kodi.get_setting('%s-username' % (self.get_name()))
        self.password = kodi.get_setting('%s-password' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'ororo.tv'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s (%s) (%s/100) ' % (item['quality'], item['host'], item['format'], item['rating'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            if video.video_type == VIDEO_TYPES.MOVIE:
                quality = QUALITIES.HD720
                match = re.search('data-href="([^"]+)', html)
                if match:
                    source_url = match.group(1)
                    url = urlparse.urljoin(self.base_url, source_url)
                    html = self._http_get(url, cache_limit=.5)
            else:
                quality = QUALITIES.HIGH

            for match in re.finditer("source src='([^']+)'\s+type='video/([^']+)", html):
                stream_url, format = match.groups()
                stream_url = stream_url + '|User-Agent=%s' % (USER_AGENT)
                hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'url': stream_url, 'quality': quality, 'views': None, 'rating': None, 'format': format, 'direct': True}
                hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(OroroTV_Scraper, self)._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        episode_pattern = 'data-href="([^"]+)[^>]*class="episode"\s+href="#%s-%s"' % (video.season, video.episode)
        title_pattern = 'data-href="([^"]+)[^>]+class="episode"[^>]+>.\d+\s+([^<]+)'
        return super(OroroTV_Scraper, self)._default_get_episode_url(show_url, video, episode_pattern, title_pattern)

    def search(self, video_type, title, year):
        url = urlparse.urljoin(self.base_url, 'http://ororo.tv/en')
        if video_type == VIDEO_TYPES.MOVIE:
            url += '/movies'
        html = self._http_get(url, cache_limit=.25)
        results = []
        norm_title = self._normalize_title(title)
        include_paid = kodi.get_setting('%s-include_premium' % (self.get_name())) == 'true'
        for match in re.finditer('<span class=\'value\'>(\d{4})(.*?)href="([^"]+)[^>]+>([^<]+)', html, re.DOTALL):
            match_year, middle, url, match_title = match.groups()
            if not include_paid and video_type == VIDEO_TYPES.MOVIE and 'paid accounts' in middle:
                continue

            if norm_title in self._normalize_title(match_title) and (not year or not match_year or year == match_year):
                result = {'url': url, 'title': match_title, 'year': match_year}
                results.append(result)

        return results

    @classmethod
    def get_settings(cls):
        settings = super(OroroTV_Scraper, cls).get_settings()
        name = cls.get_name()
        settings.append('         <setting id="%s-username" type="text" label="     %s" default="" visible="eq(-6,true)"/>' % (name, i18n('username')))
        settings.append('         <setting id="%s-password" type="text" label="     %s" option="hidden" default="" visible="eq(-7,true)"/>' % (name, i18n('password')))
        settings.append('         <setting id="%s-include_premium" type="bool" label="     %s" default="false" visible="eq(-8,true)"/>' % (name, i18n('include_premium')))
        return settings

    def _http_get(self, url, data=None, cache_limit=8):
        # return all uncached blank pages if no user or pass
        if not self.username or not self.password:
            return ''

        html = super(OroroTV_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)
        if not re.search('href="/en/users/sign_out"', html):
            log_utils.log('Logging in for url (%s)' % (url), xbmc.LOGDEBUG)
            self.__login()
            html = super(OroroTV_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=0)

        return html

    def __login(self):
        url = urlparse.urljoin(self.base_url, '/en/users/sign_in')
        data = {'user[email]': self.username, 'user[password]': self.password, 'user[remember_me]': 1}
        html = super(OroroTV_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, allow_redirect=False, cache_limit=0)
        if html != 'http://ororo.tv/en':
            raise Exception('ororo.tv login failed: %s' % (html))
