def __enum(**enums):
    return type('Enum', (), enums)

MODES=__enum(MAIN='main', BROWSE='browse', TRENDING='trending', RECOMMEND='recommend', FRIENDS='friends', CAL='calendar', MY_CAL='my_calendar', MY_LISTS='lists', 
             SEARCH='search', SEASONS='seasons', EPISODES='episodes', GET_SOURCES='get_sources', MANAGE_SUBS='manage_subs', GET_LIST='get_list', SET_URL_MANUAL='set_url_manual', 
           SET_URL_SEARCH='set_url_search', SHOW_FAVORITES='browse_favorites', SHOW_WATCHLIST='browse_watchlist', PREMIERES='premiere_calendar', SHOW_LIST='show_list', 
           OTHER_LISTS='other_lists', ADD_OTHER_LIST='add_other_list', PICK_SUB_LIST='pick_sub_list', PICK_FAV_LIST='pick_fav_list', UPDATE_SUBS='update_subs', CLEAN_SUBS='clean_subs',
           SET_SUB_LIST='set_sub_list', SET_FAV_LIST='set_fav_list', REM_FROM_LIST='rem_from_list', ADD_TO_LIST='add_to_list', ADD_TO_LIBRARY='add_to_library')
SECTIONS=__enum(TV='TV', MOVIES='Movies')
VIDEO_TYPES = __enum(TVSHOW='tvshow', MOVIE='movie', EPISODE='episode', SEASON='season')
TRAKT_SECTIONS = {SECTIONS.TV: 'shows', SECTIONS.MOVIES: 'movies'}
QUALITIES = __enum(LOW='Low', MEDIUM='Medium', HIGH='High', HD='HD')
P_MODES = __enum(THREADS=0, PROCESSES=1, NONE=2)
WATCHLIST_SLUG = 'watchlist_slug'
USER_AGENT = ("User-Agent:Mozilla/5.0 (Windows NT 6.2; WOW64)"
              "AppleWebKit/537.17 (KHTML, like Gecko)"
              "Chrome/24.0.1312.56")

# sort keys need to be defined such that "best" have highest values
# unknown (i.e. None) is always worst
SORT_KEYS = {}
SORT_KEYS['quality'] = {None: 0, QUALITIES.LOW: 1, QUALITIES.MEDIUM: 2, QUALITIES.HIGH: 3, QUALITIES.HD: 4}
SORT_LIST = ['none', 'source', 'quality', 'rating']

SORT_SIGNS = {'0': -1, '1': 1} # 0 = Best to Worst; 1 = Worst to Best

