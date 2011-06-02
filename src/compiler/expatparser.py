#Copyright (C) 2011  Gabriel Gregori Manzano
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from event import Event
import logging
import xml.parsers.expat

class ExpatParser:
    """The XML parser which goes through the transfer files."""
    
    def __init__(self, compiler):
        self.logger = logging.getLogger('compiler')
        
        self.parser = xml.parsers.expat.ParserCreate("UTF-8")
        self.parser.StartElementHandler = self.handleStartElement
        self.parser.EndElementHandler = self.handleEndElement
        
        self.compiler = compiler
        self.callStack = self.compiler.callStack
        self.handler = self.compiler.eventHandler
        
    def parse(self, input):
        self.parser.Parse(input)
    
    def handleStartElement(self, name, attrs):
        event = Event(name, attrs)
        self.callStack.push(event)
        
        result = self.callback('_start', name, event)
    
    def handleEndElement(self, name):
        event = self.callStack.pop()
        
        result = self.callback('_end', name, event)
    
    def callback(self, suffix, name, *args):
        try:
            methodName = 'handle_' + name.replace("-", "_") + suffix
            if (not hasattr(self.handler, methodName)): methodName = 'handle_default' + suffix
            method = getattr(self.handler, methodName)
            return method(*args)
        except AttributeError as ae:
            self.logger.exception(ae)
    