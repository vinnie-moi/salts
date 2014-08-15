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
from addon.common.addon import Addon
from url_dispatcher import URL_Dispatcher

_SALTS = Addon('plugin.video.1channel', sys.argv)

def main(argv=None):
    if sys.argv: argv=sys.argv
    url_dispatcher=URL_Dispatcher()

    _SALTS.log('Version: |%s| Queries: |%s|' % (_SALTS.get_version(),_SALTS.queries))
    _SALTS.log('Args: |%s|' % (argv))
    
    # don't process params that don't match our url exactly. (e.g. plugin://plugin.video.1channel/extrafanart)
    plugin_url = 'plugin://%s/' % (_SALTS.get_id())
    if argv[0] != plugin_url:
        return

    mode = _SALTS.queries.get('mode', None)
    url_dispatcher.dispatch(mode, _SALTS.queries)

if __name__ == '__main__':
    sys.exit(main())
