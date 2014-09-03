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
import urllib2
import urllib
import xbmc
from salts_lib.constants import USER_AGENT
from salts_lib import log_utils
from salts_lib.db_utils import DB_Connection

def cached_http_get(url, base_url, timeout, cookie=None, data=None, cache_limit=8):
    log_utils.log('Getting Url: %s cookie=|%s| data=|%s|' % (url, cookie, data))
    db_connection=DB_Connection()
    html = db_connection.get_cached_url(url, cache_limit)
    if html:
        log_utils.log('Returning cached result for: %s' % (url), xbmc.LOGDEBUG)
    
    try:
        if data is not None: data=urllib.urlencode(data, True)            
        request = urllib2.Request(url, data=data)
        if cookie is not None: request.add_header('Cookie', make_cookie(cookie)) 
        request.add_header('User-Agent', USER_AGENT)
        request.add_unredirected_header('Host', request.get_host())
        request.add_unredirected_header('Referer', base_url)
        response = urllib2.urlopen(request, timeout=timeout)
        html=response.read()
    except Exception as e:
        log_utils.log('Error (%s) during scraper http get: %s' % (str(e), url), xbmc.LOGWARNING)
    
    db_connection.cache_url(url, html)
    return html

def make_cookie(cookie):
    s=''
    for key in cookie:
        s += '%s=%s; ' % (key, cookie[key])
    return s[:-2]
