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
import urllib2
import urllib
import urlparse
import re
from salts_lib.db_utils import DB_Connection
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import USER_AGENT

db_connection = DB_Connection()

class WS_Scraper(scraper.Scraper):
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.base_url = 'http://watchseries.sx'
        self.timeout=timeout
    
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE])
    
    def get_name(self):
        return 'WatchSeries'
    
    def resolve_link(self, link):
        url = urlparse.urljoin(self.base_url, link)
        html = self.__http_get(url, cache_limit=0)
        match = re.search('class\s*=\s*"myButton"\s+href\s*=\s*"(.*?)"', html)
        if match:
            return match.group(1)
    
    def format_source_label(self, item):
        return '%s (%s/100)' % (item['host'], item['rating'])
    
    def get_sources(self, video_type, title, year, season='', episode=''):
        url = urlparse.urljoin(self.base_url, self.get_url(video_type, title, year, season, episode))
        html = self.__http_get(url, cache_limit=.5)
        try:
            sources=[]
            match = re.search('English Links -.*?</tbody>\s*</table>', html, re.DOTALL)
            fragment = match.group(0)
            pattern = 'href\s*=\s*"([^"]*)"\s+class\s*=\s*"buttonlink"\s+title\s*=([^\s]*).*?<span class="percent"[^>]+>\s+(\d+)%\s+</span>'
            for match in re.finditer(pattern, fragment, re.DOTALL):
                source = {'multi-part': False}
                url, host, rating = match.groups()
                source['url']=url
                source['host']=host
                source['rating']=int(rating)
                if source['rating']==60: source['rating']=None # rating seems to default to 60, so force to Unknown
                source['quality']=None
                source['class']=self
                sources.append(source)
        except Exception as e:
            log_utils.log('Failure During %s get sources: %s' % (self.get_name(), str(e)))
            
        return sources

    def get_url(self, video_type, title, year, season='', episode=''):
        temp_video_type=video_type
        if video_type == VIDEO_TYPES.EPISODE: temp_video_type=VIDEO_TYPES.TVSHOW
        url = None
 
        result = db_connection.get_related_url(temp_video_type, title, year, self.get_name())
        if result:
            url=result[0][0]
            log_utils.log('Got local related url: |%s|%s|%s|%s|%s|' % (temp_video_type, title, year, self.get_name(), url))
        else:
            results = self.search(temp_video_type, title, year)
            if results:
                url = results[0]['url']
                db_connection.set_related_url(temp_video_type, title, year, self.get_name(), url)
 
        if url and video_type==VIDEO_TYPES.EPISODE:
            result = db_connection.get_related_url(VIDEO_TYPES.EPISODE, title, year, self.get_name(), season, episode)
            if result:
                url=result[0][0]
                log_utils.log('Got local related url: |%s|%s|%s|%s|%s|%s|%s|' % (video_type, title, year, season, episode, self.get_name(), url))
            else:
                show_url = url
                url = self.__get_episode_url(show_url, season, episode)
                if url:
                    db_connection.set_related_url(VIDEO_TYPES.EPISODE, title, year, self.get_name(), url, season, episode)
         
        return url
   
    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/search/')
        search_url += urllib.quote_plus(title)
        html = self.__http_get(search_url, cache_limit=.25)
        
        pattern='<a title="watch[^"]+"\s+href="(.*?)"><b>(.*?)</b>'
        results=[]
        for match in re.finditer(pattern, html):
            url, title_year = match.groups()
            match = re.search('(.*?)\s+\((\d{4})\)', title_year)
            if match:
                title = match.group(1)
                year = match.group(2)
            else:
                title=title_year
                year=''
            result={'url': url, 'title': title, 'year': year}
            results.append(result)
        return results
    
    def __get_episode_url(self, show_url, season, episode):
        url = urlparse.urljoin(self.base_url, show_url)
        html = self.__http_get(url, cache_limit=2)
        pattern = 'href="(/episode/[^"]*_s%s_e%s.*?)"' % (season, episode)
        match = re.search(pattern, html)
        if match:
            return match.group(1)
    
    def __http_get(self, url, cache_limit=8):
        log_utils.log('Getting Url: %s' % (url))
        db_connection=DB_Connection()
        html = db_connection.get_cached_url(url, cache_limit)
        if html:
            log_utils.log('Returning cached result for: %s' % (url), xbmc.LOGDEBUG)
            return html
        
        request = urllib2.Request(url)
        request.add_header('User-Agent', USER_AGENT)
        request.add_unredirected_header('Host', request.get_host())
        request.add_unredirected_header('Referer', self.base_url)
        response = urllib2.urlopen(request, timeout=self.timeout)
        html=response.read()
        db_connection.cache_url(url, html)
        return html
        