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
import abc
abstractstaticmethod = abc.abstractmethod

DEFAULT_TIMEOUT=30

class Scraper(object):
    __metaclass__ = abc.ABCMeta
    
    @classmethod
    def provides(cls):
        """
        Must return a list/set/frozenset of VIDEO_TYPES that are supported by this scraper. Is a class method so that instances of the class 
        don't have to be instantiated to determine they are not useful
        
        * Can not easily combine classmethod and abstract method, but this method must be provided as a class method
        * Datatypes set or frozenset are preferred as existence checking is faster with sets
        """
        raise NotImplementedError
        
    @abc.abstractmethod 
    def get_name(self):
        """
        Must return a string that is a name that will be used through out the UI and DB to refer to urls from this source
        Should be descriptive enough to be recognized but short enough to be presented in the UI
        """
        raise NotImplementedError

    @abc.abstractmethod 
    def resolve_link(self, link):
        """
        Must return a string that is a urlresolver resolvable link given a link that this scraper supports
        
        link: a url fragment associated with this site that can be resolved to a hoster link 

        * The purpose is many streaming sites provide the actual hoster link in a separate page from link
        on the video page.
        * This method is called for the user selected source before calling urlresolver on it.
        """
        raise NotImplementedError

    @abc.abstractmethod 
    def format_source_label(self, item):
        """
        Must return a string that is to be the label to be used for this source in the "Choose Source" dialog
        
        item: one element of the list that is returned from get_sources for this scraper
        """
        raise NotImplementedError

    @abc.abstractmethod 
    def get_sources(self, video_type, title, year, season='', episode=''):
        """
        Must return a list of dictionaries that are potential link to hoster sites (or links to links to hoster sites)
        Each dictionary must contain elements of at least:
            * multi-part: True if this source is one part of a whole
            * class: a reference to an instance of the scraper itself
            * url: the url that is a link to a hoster, or a link to a page that this scraper can resolve to a link to a hoster
            * quality: one of the QUALITIES values, or None if unknown; users can sort sources by quality
            * views: count of the views from the site for this source or None is unknown; Users can sort sources by views
            * rating: a value between 0 and 100; 0 being worst, 100 the best, or None if unknown. Users can sort sources by rating. 
            * other keys are allowed as needed if they would be useful (e.g. for format_source_label)
        
        video_type: one of VIDEO_TYPES for whatever the sources should be for
        title: the title of the tv show or movie
        year: the year of the tv show or movie
        season: only present for tv shows; the season number of the video for which sources are requested
        episode: only present for tv shows; the episode number of the video for which sources are requested        
        """
        raise NotImplementedError

    @abc.abstractmethod 
    def get_url(self, video_type, title, year, season='', episode=''):
        """
        Must return a url for the site this scraper is associated with that is related to this video.
        
        video_type: one of VIDEO_TYPES this url is for (e.g. EPISODE urls might be different than TVSHOW urls)
        title: the title of the tv show or movie
        year: the year of the tv show or movie
        season: only present for season or episode VIDEO_TYPES; the season number for the url being requested
        episode: only present for season or episode VIDEO_TYPES; the episode number for the url being requested
        
        * Generally speaking, domain should not be included
        """
        raise NotImplementedError

    @abc.abstractmethod 
    def search(self, video_type, title, year):
        """
        Must return a list of results returned from the site associated with this scraper when doing a search using the input parameters
        
        If it does return results, it must be a list of dictionaries. Each dictionary must contain at least the following:
            * title: title of the result
            * year: year of the result
            * url: a url fragment that is the url on the site associated with this scraper for this season result item
        
        video_type: one of the VIDEO_TYPES being searched for. Only tvshows and movies are expected generally
        title: the title being search for
        year: the year being search for
        
        * Method must be provided, but can raise NotImplementedError if search not available on the site
        """
        raise NotImplementedError
