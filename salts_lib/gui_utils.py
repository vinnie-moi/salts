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
import xbmcgui
from salts_lib import log_utils
from addon.common.addon import Addon

_SALTS = Addon('plugin.video.salts', sys.argv)

def get_pin():
    AUTH_BUTTON = 200
    LATER_BUTTON = 201
    NEVER_BUTTON = 202
    ACTION_PREVIOUS_MENU = 10
    ACTION_BACK = 92
    
    class PinAuthDialog(xbmcgui.WindowXMLDialog):
        def onInit(self):
            pass

        def onAction(self, action):
            print 'Action: %s' % (action.getId())
            if action == ACTION_PREVIOUS_MENU or action == ACTION_BACK:
                self.close()

        def onControl(self, control):
            print 'onControl: %s' % (control)
            pass

        def onFocus(self, control):
            print 'onFocus: %s' % (control)
            pass

        def onClick(self, control):
            print 'onClick: %s' % (control)
            if control == AUTH_BUTTON:
                if not self.__get_token():
                    return

            if control == LATER_BUTTON:
                # record last shown
                pass

            if control == NEVER_BUTTON:
                self.search = False

            if control in [AUTH_BUTTON, LATER_BUTTON, NEVER_BUTTON]:
                self.close()
        
        def __get_token(self):
            return True

    dialog = PinAuthDialog('TraktPinAuthDialog.xml', _SALTS.get_path())
    dialog.doModal()