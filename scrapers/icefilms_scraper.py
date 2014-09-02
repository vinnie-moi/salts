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
import common
from salts_lib.db_utils import DB_Connection
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

QUALITY_MAP = {'HD 720P': QUALITIES.HD, 'DVDRIP / STANDARD DEF': QUALITIES.HIGH}
BROKEN_RESOLVERS = ['180UPLOAD', 'HUGEFILES', 'VIDPLAY']

class PW_Scraper(scraper.Scraper):
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.base_url = 'http://www.icefilms.info/'
        self.timeout=timeout
        self.db_connection = DB_Connection()
   
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])
    
    def get_name(self):
        return 'IceFilms'
    
    def resolve_link(self, link):
        url, query = link.split('?', 1)
        data = urlparse.parse_qs(query, True)
        url = urlparse.urljoin(self.base_url, url)
        html = self.__http_get(url, data=data, cache_limit=0)
        match = re.search('url=(.*)', html)
        if match:
            url=urllib.unquote_plus(match.group(1))
            if url.upper() in BROKEN_RESOLVERS:
                url = None
            return url
    
    def format_source_label(self, item):
        label='[%s] %s%s (%s/100) ' % (item['quality'], item['label'], item['host'], item['rating'])
        return label
    
    def get_sources(self, video_type, title, year, season='', episode=''):
        source_url=self.get_url(video_type, title, year, season, episode)
        sources = []
        if source_url:
            try:
                url = urlparse.urljoin(self.base_url, source_url)
                html = self.__http_get(url, cache_limit=.5)
                
                pattern='<iframe id="videoframe" src="([^"]+)'
                match = re.search(pattern, html)
                frame_url = match.group(1)
                url = urlparse.urljoin(self.base_url, frame_url)
                html = self.__http_get(url, cache_limit=.5)
                
                match=re.search('lastChild\.value="([^"]+)"', html)
                secret=match.group(1)
                        
                match=re.search('"&t=([^"]+)', html)
                t=match.group(1)
                        
                pattern='<div class=ripdiv>(.*?)</div>'
                for container in re.finditer(pattern, html):
                    fragment=container.group(0)
                    match=re.match('<div class=ripdiv><b>(.*?)</b>', fragment)
                    if match:
                        quality=QUALITY_MAP[match.group(1).upper()]
                    else:
                        quality=None
                    
                    pattern='onclick=\'go\((\d+)\)\'>([^<]+)(<span.*?)</a>'
                    for match in re.finditer(pattern, fragment):
                        link_id, label, host_fragment = match.groups()
                        source = {'multi-part': False}
                        source['host']=re.sub('(<[^>]+>|</span>)','',host_fragment)
                        if source['host'].upper() in BROKEN_RESOLVERS:
                            continue

                        url = '/membersonly/components/com_iceplayer/video.phpAjaxResp.php?id=%s&s=999&iqs=&url=&m=-999&cap=&sec=%s&t=%s' % (link_id, secret, t)
                        source['url']=url
                        source['quality']=quality
                        source['class']=self
                        source['label']=label
                        source['rating']=None
                        source['views']=None
                        sources.append(source)
            except Exception as e:
                log_utils.log('Failure (%s) during get sources: |%s|%s|%s|%s|%s|' % (str(e), video_type, title, year, season, episode))
        return sources

    def get_url(self, video_type, title, year, season='', episode=''):
        temp_video_type=video_type
        if video_type == VIDEO_TYPES.EPISODE: temp_video_type=VIDEO_TYPES.TVSHOW
        url = None

        result = self.db_connection.get_related_url(temp_video_type, title, year, self.get_name())
        if result:
            url=result[0][0]
            log_utils.log('Got local related url: |%s|%s|%s|%s|%s|' % (temp_video_type, title, year, self.get_name(), url))

        if url and video_type==VIDEO_TYPES.EPISODE:
            result = self.db_connection.get_related_url(VIDEO_TYPES.EPISODE, title, year, self.get_name(), season, episode)
            if result:
                url=result[0][0]
                log_utils.log('Got local related url: |%s|%s|%s|%s|%s|%s|%s|' % (video_type, title, year, season, episode, self.get_name(), url))
            else:
                show_url = url
                url = self.__get_episode_url(show_url, season, episode)
                if url:
                    self.db_connection.set_related_url(VIDEO_TYPES.EPISODE, title, year, self.get_name(), url, season, episode)
        
        return url
    
    def search(self, video_type, title, year):
        raise NotImplementedError
    
    def __get_episode_url(self, show_url, season, episode):
        url = urlparse.urljoin(self.base_url, show_url)
        html = self.__http_get(url, cache_limit=2)
        pattern = 'href=(/ip\.php[^>]+)>%sx0?%s\s+' % (season, episode)
        match = re.search(pattern, html)
        if match:
            url = match.group(1)
            return url.replace(self.base_url, '')
        
    def __http_get(self, url, data=None, cache_limit=8):
        return common.cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)
