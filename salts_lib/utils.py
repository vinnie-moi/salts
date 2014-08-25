import time
import re
import xbmc
import xbmcgui
import log_utils
from constants import *
from addon.common.addon import Addon
from trakt_api import Trakt_API
from db_utils import DB_Connection

ADDON = Addon('plugin.video.salts')
username=ADDON.get_setting('username')
password=ADDON.get_setting('password')
use_https=ADDON.get_setting('use_https')=='true'

trakt_api=Trakt_API(username,password, use_https)
db_connection=DB_Connection()

def choose_list(username=None):
    lists = trakt_api.get_lists(username)
    lists.insert(0, {'name': 'watchlist', 'slug': WATCHLIST_SLUG})
    dialog=xbmcgui.Dialog()
    index = dialog.select('Pick a list', [list_data['name'] for list_data in lists])
    if index>-1:
        return lists[index]['slug']

def show_id(show):
    queries={}
    if 'imdb_id' in show:
        queries['id_type']='imdb_id'
        queries['show_id']=show['imdb_id']
    elif 'tvdb_id' in show:
        queries['id_type']='tvdb_id'
        queries['show_id']=show['tvdb_id']
    elif 'tmdb_id' in show:
        queries['id_type']='tmdb_id'
        queries['show_id']=show['tmdb_id']
    return queries
    
def update_url(video_type, title, year, source, old_url, new_url, season, episode):
    log_utils.log('Setting Url: |%s|%s|%s|%s|%s|%s|%s|%s|' % (video_type, title, year, source, old_url, new_url, season, episode), xbmc.LOGDEBUG)
    if new_url:
        db_connection.set_related_url(video_type, title, year, source, new_url, season, episode)
    else:
        db_connection.clear_related_url(video_type, title, year, source, season, episode)

    # clear all episode local urls if tvshow url changes
    if video_type == VIDEO_TYPES.TVSHOW and new_url != old_url:
        db_connection.clear_related_url(VIDEO_TYPES.EPISODE, title, year, source)
    
def make_season_item(season, fanart):
    label = 'Season %s' % (season['season'])
    season['images']['fanart']=fanart
    liz=make_list_item(label, season)
    liz.setInfo('video', {'season': season['season']})

    menu_items=[]
    liz.addContextMenuItems(menu_items, replaceItems=True)
    return liz

def make_list_item(label, meta):
    art=make_art(meta)
    listitem = xbmcgui.ListItem(label, iconImage=art['thumb'], thumbnailImage=art['thumb'])
    listitem.setProperty('fanart_image', art['fanart'])
    try: listitem.setArt(art)
    except: pass
    if 'imdb_id' in meta: listitem.setProperty('imdb_id', meta['imdb_id'])
    if 'tvdb_id' in meta: listitem.setProperty('tvdb_id', str(meta['tvdb_id']))
    return listitem

def make_art(show, fanart=''):
    art={'banner': '', 'fanart': fanart, 'thumb': '', 'poster': ''}
    if 'images' in show:
        if 'banner' in show['images']: art['banner']=show['images']['banner']
        if 'fanart' in show['images']: art['fanart']=show['images']['fanart']
        if 'poster' in show['images']: art['thumb']=art['poster']=show['images']['poster']
        if 'screen' in show['images']: art['thumb']=art['poster']=show['images']['screen']
    return art

def make_info(item, show=''):
    log_utils.log('Making Info: Show: %s' % (show), xbmc.LOGDEBUG)
    log_utils.log('Making Info: Item: %s' % (item), xbmc.LOGDEBUG)
    info={}
    info['title']=item['title']
    info['rating']=int(item['ratings']['percentage'])/10.0
    info['votes']=item['ratings']['votes']
    info['plot']=info['plotoutline']=item['overview']
    
    if 'runtime' in item: info['duration']=item['runtime']
    if 'imdb_id' in item: info['code']=item['imdb_id']
    if 'certification' in item: info['mpaa']=item['certification']
    if 'year' in item: info['year']=item['year']
    if 'season' in item: info['season']=item['season']
    if 'episode' in item: info['episode']=item['episode']
    if 'number' in item: info['episode']=item['number']
    if 'genres' in item: info['genre']=', '.join(item['genres'])
    if 'network' in item: info['studio']=item['network']
    if 'first_aired' in item: info['aired']=info['premiered']=time.strftime('%Y-%m-%d', time.localtime(item['first_aired']))
    if 'released' in item: info['premiered']=time.strftime('%Y-%m-%d', time.localtime(item['released']))
    if 'status' in item: info['status']=item['status']
    if 'tagline' in item: info['tagline']=item['tagline']

    # override item params with show info if it exists
    if 'certification' in show: info['mpaa']=show['certification']
    if 'year' in show: info['year']=show['year']
    if 'imdb_id' in show: info['code']=show['imdb_id']
    if 'runtime' in show: info['duration']=show['runtime']
    if 'title' in show: info['tvshowtitle']=show['title']
    if 'people' in show: info['cast']=[actor['name'] for actor in show['people']['actors'] if actor['name']]
    if 'people' in show: info['castandrole']=['%s as %s' % (actor['name'],actor['character']) for actor in show['people']['actors'] if actor['name'] and actor['character']]
    return info
    
def get_section_params(section):
    section_params={}
    section_params['section']=section
    if section==SECTIONS.TV:
        section_params['next_mode']=MODES.SEASONS
        section_params['folder']=True
        section_params['video_type']=VIDEO_TYPES.TVSHOW
    else:
        section_params['next_mode']=MODES.GET_SOURCES
        section_params['folder']=False
        section_params['video_type']=VIDEO_TYPES.MOVIE
    return section_params

def filename_from_title(title, video_type):
    if video_type == VIDEO_TYPES.TVSHOW:
        filename = '%s S%sE%s.strm'
        filename = filename % (title, '%s', '%s')
    else:
        filename = '%s.strm' % title

    filename = re.sub(r'(?!%s)[^\w\-_\.]', '.', filename)
    filename = re.sub('\.+', '.', filename)
    xbmc.makeLegalFilename(filename)
    return filename
