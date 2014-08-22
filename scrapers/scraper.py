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

class Scraper(object):
    __metaclass__ = abc.ABCMeta
    
    @classmethod
    def provides(cls):
        """
        Can not easily combine classmethod and abstract method, but must method be provided as a class method
        """
        raise NotImplementedError
        
    @abc.abstractmethod 
    def get_name(self):
        raise NotImplementedError

    @abc.abstractmethod 
    def resolve_link(self, link):
        raise NotImplementedError

    @abc.abstractmethod 
    def format_source_label(self, item):
        raise NotImplementedError

    @abc.abstractmethod 
    def get_sources(self, video_type, title, year, season='', episode=''):
        raise NotImplementedError

    @abc.abstractmethod 
    def get_url(self, video_type, title, year, season='', episode=''):
        raise NotImplementedError

    @abc.abstractmethod 
    def search(self, video_type, title, year):
        """
        Method must be provided, but can throw NotImplementedError if not available
        """
        raise NotImplementedError
