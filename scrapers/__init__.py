__all__ = ['scraper', 'dummy_scraper', 'pw_scraper', 'uflix_scraper', 'watchseries_scraper', 'movie25_scraper', 'merdb_scraper', '2movies_scraper', 'icefilms_scraper', 'afdah_scraper']

import re
import os
import xbmcaddon
from . import scraper # just to avoid editor warning
from . import *

def update_settings():
    path=xbmcaddon.Addon().getAddonInfo('path')
    full_path = os.path.join(path, 'resources', 'settings.xml')
    print full_path
    xml=''
    try:
        with open(full_path, 'r') as f:
            xml=f.read()
    except:
        pass
    
    match = re.search('(<category label="Scrapers">.*?</category>)', xml, re.DOTALL | re.I)
    if match:
        old_settings=match.group(1)
        
        new_settings = '<category label="Scrapers">\n'
        classes=scraper.Scraper.__class__.__subclasses__(scraper.Scraper)
        for cls in classes:
            for setting in cls.get_settings(): new_settings += setting + '\n'
        new_settings += '    </category>'
            
        if old_settings != new_settings:
            xml=xml.replace(old_settings, new_settings)
            with open(full_path, 'w') as f:
                f.write(xml)
        else:
            print 'don\'t need to update settings'
    else:
        print 'unable to match scraper category'

update_settings()