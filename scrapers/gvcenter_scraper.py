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
import xbmc
import urllib
import urlparse
import re
import json
import base64
import time
import hashlib
import random
import string
from salts_lib import pyaes
from salts_lib import log_utils
from salts_lib import kodi
from salts_lib.constants import VIDEO_TYPES

BASE_URL = 'http://gearscenter.com'
API_URL = '/gold-server/gapiandroid207/'
SEARCH_DATA = {'option': 'search', 'page': 1, 'total': 0, 'block': 0}
CONTENT_DATA = {'option': 'content'}
SOURCE_DATA = {'option': 'filmcontent'}
CONFIG_DATA = {'option': 'config'}

RESULT_URL = '/video_type=%s&catalog_id=%s'
EPISODE_URL = RESULT_URL + '&season=%s&episode=%s'
ANDROID_LEVELS = {'22': '5.1.0', '21': '5.0', '19': '4.4.4', '18': '4.3.0', '17': '4.2.0', '16': '4.1.0', '15': '4.0.4', '14': '4.0.2', '13': '3.2.0'}
VN = urllib.quote_plus('2.0.7')
VC = urllib.quote_plus(str(207).encode('utf-8'))
PN = hashlib.md5('com.dnproteam.funboxhd').hexdigest().upper()
FILM_KEY = hashlib.md5(VC + VN + PN).hexdigest()[0:16]
GV_USER_AGENT = "Apache-HttpClient/UNAVAILABLE (java 1.4)"
HEADERS = {'User-Agent': GV_USER_AGENT}

class GVCenter_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))
        self.last_call = 0
        self.access_token = kodi.get_setting('%s-access_token' % (self.get_name()))
        device_id = kodi.get_setting('%s-device_id' % (self.get_name()))
        if device_id not in ['', '0']:
            self.device_id = device_id
        else:
            self.device_id = None

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'GVCenter'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        if 'resolution' in item:
            return '[%s] (%s) %s' % (item['quality'], item['resolution'], item['host'])
        else:
            return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        sources = []
        if source_url:
            params = urlparse.parse_qs(source_url)
            catalog_id = params['catalog_id'][0]
            sid = hashlib.md5('content%scthd' % (catalog_id)).hexdigest()
            url = urlparse.urljoin(self.base_url, API_URL)
            data = CONTENT_DATA
            data.update({'id': catalog_id, 'sid': sid})
            html = self._http_get(url, data=data)
            try:
                js_data = json.loads(html)
                if video.video_type == VIDEO_TYPES.EPISODE:
                    js_data = self.__get_episode_json(params, js_data)
            except ValueError:
                log_utils.log('Invalid JSON returned for: %s' % (url), xbmc.LOGWARNING)
            else:
                for film in js_data['listvideos']:
                    film_id = film['film_id']
                    sid = hashlib.md5('%s%scthd' % (film_id, catalog_id)).hexdigest()
                    data = SOURCE_DATA
                    data.update({'id': film_id, 'cataid': catalog_id, 'sid': sid})
                    url = urlparse.urljoin(self.base_url, API_URL)
                    html = self._http_get(url, data=data)
                    try:
                        film_js = json.loads(html)
                    except ValueError:
                        log_utils.log('Invalid JSON returned for: %s' % (url), xbmc.LOGWARNING)
                    else:
                        for film in film_js['videos']:
                            film_link = self.__decrypt(FILM_KEY, base64.b64decode(film['film_link']))
                            for match in re.finditer('(http.*?(?:#(\d+)#)?)(?=http|$)', film_link):
                                link, height = match.groups()
                                source = {'multi-part': False, 'url': link, 'host': self._get_direct_hostname(link), 'class': self, 'quality': self._gv_get_quality(link), 'views': None, 'rating': None, 'direct': True}
                                if height is not None: source['resolution'] = '%sp' % (height)
                                sources.append(source)

        return sources

    def __get_episode_json(self, params, js_data):
            new_data = {'listvideos': []}
            for episode in js_data['listvideos']:
                if ' S%02dE%02d ' % (int(params['season'][0]), int(params['episode'][0])) in episode['film_name']:
                    new_data['listvideos'].append(episode)
            return new_data

    def get_url(self, video):
        return super(GVCenter_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        results = []
        data = SEARCH_DATA
        data['q'] = title
        url = urlparse.urljoin(self.base_url, API_URL)
        html = self._http_get(url, data=data)
        try:
            js_data = json.loads(html)
        except ValueError:
            log_utils.log('Invalid JSON returned for: %s' % (data), xbmc.LOGWARNING)
        else:
            for item in js_data['categories']:
                match = re.search('(.*?)\s+\((\d{4}).?\d{0,4}\s*\)', item['catalog_name'])
                if match:
                    match_title, match_year = match.groups()
                else:
                    match_title = item['catalog_name']
                    match_year = ''
                
                if not year or not match_year or year == match_year:
                    result_url = RESULT_URL % (video_type, item['catalog_id'])
                    result = {'title': match_title, 'url': result_url, 'year': match_year}
                    results.append(result)
        return results

    def _get_episode_url(self, show_url, video):
        params = urlparse.parse_qs(show_url)
        catalog_id = params['catalog_id'][0]
        sid = hashlib.md5('content%scthd' % (catalog_id)).hexdigest()
        url = urlparse.urljoin(self.base_url, API_URL)
        data = CONTENT_DATA
        data.update({'id': catalog_id, 'sid': sid})
        html = self._http_get(url, data=data)
        try:
            js_data = json.loads(html)
        except ValueError:
            log_utils.log('Invalid JSON returned for: %s' % (url), xbmc.LOGWARNING)
        else:
            force_title = self._force_title(video)
            if not force_title:
                for episode in js_data['listvideos']:
                    if ' S%02dE%02d ' % (int(video.season), int(video.episode)) in episode['film_name']:
                        return EPISODE_URL % (video.video_type, params['catalog_id'][0], video.season, video.episode)
            
            if (force_title or kodi.get_setting('title-fallback') == 'true') and video.ep_title:
                norm_title = self._normalize_title(video.ep_title)
                for episode in js_data['listvideos']:
                    match = re.search('-\s*S(\d+)E(\d+)\s*-\s*(.*)', episode['film_name'])
                    if match:
                        season, episode, title = match.groups()
                        if title and norm_title == self._normalize_title(title):
                            return EPISODE_URL % (video.video_type, params['catalog_id'][0], int(season), int(episode))

    @classmethod
    def get_settings(cls):
        settings = super(GVCenter_Scraper, cls).get_settings()
        name = cls.get_name()
        settings.append('         <setting id="%s-last-config" type="number" default="0" visible="false"/>' % (name))
        settings.append('         <setting id="%s-device_id" type="number" default="0" visible="false"/>' % (name))
        settings.append('         <setting id="%s-access_token" type="text" default="" visible="false"/>' % (name))
        return settings

    def _http_get(self, url, data=None, cache_limit=0):
        if not self.access_token: return ''
        now = int(time.time())
        self.__check_config()
        data.update(self.__get_extra(now))
        # throttle http requests
        #while time.time() - self.last_call < 2: time.sleep(.25)
        result = super(GVCenter_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, headers=HEADERS, cache_limit=cache_limit)
        #self.last_call = time.time()
        try:
            #print 'result: %s' % (result)
            js_data = json.loads(result)
        except ValueError:
            log_utils.log('Invalid JSON returned for: %s' % (url), xbmc.LOGWARNING)
        else:
            if 'data' in js_data:
                key = hashlib.md5('cthd' + str(now)).hexdigest()[0:16]
                return self.__decrypt(key, base64.b64decode(js_data['data']))
        return ''
                    
    def __check_config(self):
        now = int(time.time())
        last_config_call = now - int(kodi.get_setting('%s-last-config' % (self.get_name())))
        if self.device_id is None or last_config_call > 8 * 60 * 60:
            data = CONFIG_DATA
            self.device_id = ''.join(random.choice(string.digits) for _ in xrange(15))
            kodi.set_setting('%s-device_id' % (self.get_name()), self.device_id)
            data.update(self.__get_extra(now))
            url = urlparse.urljoin(self.base_url, API_URL)
            _html = super(GVCenter_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, headers=HEADERS, cache_limit=0)
            kodi.set_setting('%s-last-config' % (self.get_name()), str(int(now)))
    
    def __get_extra(self, now):
        build = random.choice(ANDROID_LEVELS.keys())
        device_name = 'Google-Nexus-6---%s---API-%s' % (ANDROID_LEVELS[build], build)
        return {'os': 'android', 'version': VN, 'versioncode': VC, 'param_1': PN, 'deviceid': self.device_id, 'devicename': device_name, 'access_token': self.access_token, 'time': now}
    
    def __decrypt(self, key, cipher_text):
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationECB(key))
        plain_text = decrypter.feed(cipher_text)
        plain_text += decrypter.feed()
        return plain_text
