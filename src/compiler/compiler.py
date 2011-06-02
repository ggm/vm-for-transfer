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

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import logging
from expatparser import ExpatParser
from callstack import CallStack
from eventhandler import EventHandler

class Compiler:
    """This class encapsulates all the compiling process."""
    
    def __init__(self):
        self.logger = logging.getLogger('compiler')
        self.logger.setLevel(logging.INFO)
        
        #We use 'buffer' to get a stream of bytes, not str.
        self.input = sys.stdin.buffer
        self.output = sys.stdout.buffer
        
        #Create all the data structures needed.
        self.defCats = {}
        
        #Initialize all the compiler's components.
        self.callStack = CallStack()
        self.eventHandler = EventHandler(self)
        self.parser = ExpatParser(self)
        
    def compile(self):
        self.parser.parse(self.input.read())

