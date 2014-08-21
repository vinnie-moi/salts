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
import sys
import time
import xbmcplugin
import xbmcgui
import xbmc
from addon.common.addon import Addon
from salts_lib.db_utils import DB_Connection
from salts_lib.url_dispatcher import URL_Dispatcher
from salts_lib.trakt_api import Trakt_API
from salts_lib import utils
from salts_lib.utils import MODES
from salts_lib.utils import SECTIONS
from salts_lib.utils import VIDEO_TYPES
from scrapers import * # import all scrapers into this namespace

url_dispatcher=URL_Dispatcher()
db_connection=DB_Connection()
_SALTS = Addon('plugin.video.salts', sys.argv)
username=_SALTS.get_setting('username')
password=_SALTS.get_setting('password')
use_https=_SALTS.get_setting('use_https')=='true'
trakt_api=Trakt_API(username,password, use_https)

@url_dispatcher.register(MODES.MAIN)
def main_menu():
    db_connection.init_database()
    _SALTS.add_directory({'mode': MODES.BROWSE, 'section': SECTIONS.MOVIES}, {'title': 'Movies'})
    _SALTS.add_directory({'mode': MODES.BROWSE, 'section': SECTIONS.TV}, {'title': 'TV Shows'})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.BROWSE, ['section'])
def browse_menu(section):
    section_label='TV Shows' if section==SECTIONS.TV else 'Movies'
    _SALTS.add_directory({'mode': MODES.TRENDING, 'section': section}, {'title': 'Trending %s' % (section_label)})
    _SALTS.add_directory({'mode': MODES.RECOMMEND, 'section': section}, {'title': 'Recommended %s' % (section_label)})
    _SALTS.add_directory({'mode': MODES.FRIENDS, 'section': section}, {'title': 'Friends Activity'})
    _SALTS.add_directory({'mode': MODES.LISTS}, {'title': 'My Lists'})
    _SALTS.add_directory({'mode': MODES.SEARCH, 'section': section}, {'title': 'Search'})
    if section==SECTIONS.TV:
        _SALTS.add_directory({'mode': MODES.MANAGE_SUBS}, {'title': 'Manage Subscriptions'})
        _SALTS.add_directory({'mode': MODES.CAL}, {'title': 'Calendar'})
        _SALTS.add_directory({'mode': MODES.MY_CAL}, {'title': 'My Calendar'})
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.TRENDING, ['section'])
def browse_trending(section):
    section_params=get_section_params(section)
    shows=trakt_api.get_trending(section)
    totalItems=len(shows)
    for show in shows:
        liz, liz_url =make_item(section_params, show)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz, isFolder=section_params['folder'], totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.RECOMMEND, ['section'])
def browse_recommendations(section):
    section_params=get_section_params(section)
    shows=trakt_api.get_recommendations(section)
    totalItems=len(shows)
    for show in shows:
        liz, liz_url =make_item(section_params, show)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz,isFolder=section_params['folder'],totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.FRIENDS, ['section'])
def browse_friends(section):
    section_params=get_section_params(section)
    activities=trakt_api.get_friends_activity(section)
    totalItems=len(activities)
    
    for activity in activities['activity']:
        liz, liz_url =make_item(section_params, activity[section_params['video_type']])

        label=liz.getLabel()
        label += ' (%s %s' % (activity['user']['username'], activity['action'])
        if activity['action']=='rating': label += ' - %s' % (activity['rating'])
        label += ')'
        liz.setLabel(label)
        
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz,isFolder=section_params['folder'],totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.CAL)
def browse_calendar():
    days=trakt_api.get_calendar()
    totalItems=len(days)
    for day in days:
        date=day['date']
        for episode_elem in day['episodes']:
            show=episode_elem['show']
            episode=episode_elem['episode']
            fanart=show['images']['fanart']
            liz=make_episode_item(show, episode, fanart)
            slug=trakt_api.get_slug(show['url'])
            queries = {'mode': MODES.GET_SOURCES, 'slug': slug, 'season': episode['season'], 'episode': episode['number']}
            liz_url = _SALTS.build_plugin_url(queries)
            label=liz.getLabel()
            print date,label
            label = '[%s] %s - %s' % (date, show['title'], label.decode('utf-8', 'replace'))
            liz.setLabel(label)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz,isFolder=False,totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.MY_CAL)
def browse_my_calendar():
    days=trakt_api.get_my_calendar()
    totalItems=len(days)
    for day in days:
        date=day['date']
        for episode_elem in day['episodes']:
            show=episode_elem['show']
            episode=episode_elem['episode']
            fanart=show['images']['fanart']
            liz=make_episode_item(show, episode, fanart)
            slug=trakt_api.get_slug(show['url'])
            queries = {'mode': MODES.GET_SOURCES, 'slug': slug, 'season': episode['season'], 'episode': episode['number']}
            liz_url = _SALTS.build_plugin_url(queries)
            label=liz.getLabel()
            print date,label
            label = '[%s] %s - %s' % (date, show['title'], label.decode('utf-8', 'replace'))
            liz.setLabel(label)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz,isFolder=False,totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.LISTS)
def browse_lists():
    pass

@url_dispatcher.register(MODES.SEARCH, ['section'])
def search(section):
    keyboard = xbmc.Keyboard()
    keyboard.setHeading('Search %s' % (section))
    while True:
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_text = keyboard.getText()
            if not search_text:
                _SALTS.show_ok_dialog(['Blank searches are not allowed'], title=_SALTS.get_name())
                continue
            else:
                break
        else:
            break
    
    if keyboard.isConfirmed():
        section_params=get_section_params(section)
        results = trakt_api.search(section, keyboard.getText())
        totalItems=len(results)
        for result in results:
            liz, liz_url =make_item(section_params, result)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz, isFolder=section_params['folder'], totalItems=totalItems)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    
@url_dispatcher.register(MODES.SEASONS, ['slug', 'fanart'])
def browse_seasons(slug, fanart):
    seasons=trakt_api.get_seasons(slug)
    totalItems=len(seasons)
    for season in reversed(seasons):
        liz=make_season_item(season, fanart)
        queries = {'mode': MODES.EPISODES, 'slug': slug, 'season': season['season'], 'fanart': fanart}
        liz_url = _SALTS.build_plugin_url(queries)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz,isFolder=True,totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.EPISODES, ['slug', 'season', 'fanart'])
def browse_episodes(slug, season, fanart):
    show=trakt_api.get_show_details(slug)
    episodes=trakt_api.get_episodes(slug, season)
    totalItems=len(episodes)
    for episode in episodes:
        liz=make_episode_item(show, episode, fanart)
        queries = {'mode': MODES.GET_SOURCES, 'video_type': VIDEO_TYPES.EPISODE, 'title': show['title'], 'year': show['year'], 'season': episode['season'], 'episode': episode['episode']}
        liz_url = _SALTS.build_plugin_url(queries)
        liz.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), liz_url, liz,isFolder=False,totalItems=totalItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

@url_dispatcher.register(MODES.GET_SOURCES, ['video_type', 'title', 'year'], ['season', 'episode'])
def get_sources(video_type, title, year, season='', episode=''):
    import urlresolver
    classes=scraper.Scraper.__class__.__subclasses__(scraper.Scraper)
    hosters=[]
    for cls in classes:
        hosters  += cls().get_sources(video_type, title, year, season, episode)
    
    sources=[]
    for item in hosters:
        try:
            # TODO: Skip multiple sources for now
            if item['multi-part']:
                continue
            
            label = item['class'].format_source_label(item)
            label = '[%s] %s' % (item['class'].get_name(),label)
            url=item['class'].resolve_link(item['url'])
            hosted_media = urlresolver.HostedMediaFile(url=url, title=label)
            sources.append(hosted_media)
        except Exception as e:
            utils.log('Error (%s) while trying to resolve %s' % (str(e), item['url']), xbmc.LOGERROR)
    
    source = urlresolver.choose_source(sources)
    if source:
        url=source.get_url()
    else:
        return
    
    utils.log('Attempting to play url: %s' % url)
    stream_url = urlresolver.HostedMediaFile(url=url).resolve()

    #If urlresolver returns false then the video url was not resolved.
    if not stream_url or not isinstance(stream_url, basestring):
        return False

    listitem = xbmcgui.ListItem(path=url, iconImage='', thumbnailImage='')
    listitem.setProperty('IsPlayable', 'true')
    listitem.setPath(stream_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    return True
    
def make_season_item(season, fanart):
    label = 'Season %s' % (season['season'])
    season['images']['fanart']=fanart
    liz=make_list_item(label, season)
    liz.setInfo('video', {'season': season['season']})

    menu_items=[]
    liz.addContextMenuItems(menu_items, replaceItems=True)
    return liz

def make_episode_item(show, episode, fanart):
    if 'episode' in episode: episode_num=episode['episode']
    else:  episode_num=episode['number']
    label = '%sx%s %s' % (episode['season'], episode_num, episode['title'])
    meta=make_info(episode, show)
    meta['images']={}
    meta['images']['poster']=episode['images']['screen']
    meta['images']['fanart']=fanart
    liz=make_list_item(label, meta)
    del meta['images']
    liz.setInfo('video', meta)
    
    menu_items=[]
    menu_items.append(('Show Information', 'XBMC.Action(Info)'), )
    liz.addContextMenuItems(menu_items, replaceItems=True)
    return liz

def make_item(section_params, show):
    label = '%s (%s)' % (show['title'], show['year'])
    liz=make_list_item(label, show)
    liz.setProperty('slug', trakt_api.get_slug(show['url']))
    liz.setInfo('video', make_info(show))
    if not section_params['folder']:
        liz.setProperty('IsPlayable', 'true')

    menu_items=[]
    menu_items.append(('Show Information', 'XBMC.Action(Info)'), )
    liz.addContextMenuItems(menu_items, replaceItems=True)

    if section_params['section']==SECTIONS.TV:
        queries = {'mode': section_params['next_mode'], 'slug': liz.getProperty('slug'), 'fanart': liz.getProperty('fanart_image')}
    else:
        queries = {'mode': section_params['next_mode'], 'video_type': section_params['video_type'], 'title': show['title'], 'year': show['year']}

    liz_url = _SALTS.build_plugin_url(queries)

    return liz, liz_url

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
    return art

def make_info(item, show=''):
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
        section_params['video_type']='show'
    else:
        section_params['next_mode']=MODES.GET_SOURCES
        section_params['folder']=False
        section_params['video_type']='movie'
    return section_params
        
def main(argv=None):
    if sys.argv: argv=sys.argv

    utils.log('Version: |%s| Queries: |%s|' % (_SALTS.get_version(),_SALTS.queries))
    utils.log('Args: |%s|' % (argv))
    
    # don't process params that don't match our url exactly. (e.g. plugin://plugin.video.1channel/extrafanart)
    plugin_url = 'plugin://%s/' % (_SALTS.get_id())
    if argv[0] != plugin_url:
        return

    mode = _SALTS.queries.get('mode', None)
    url_dispatcher.dispatch(mode, _SALTS.queries)

if __name__ == '__main__':
    sys.exit(main())
