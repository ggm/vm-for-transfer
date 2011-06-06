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

import logging

class CallStack:
    """This class represents a stack of events."""
    
    def __init__(self):
        self.logger = logging.getLogger('compiler.callstack')
        self.stack = []
        
    def push(self, value):
        self.stack.append(value)
        
    def pop(self):
        try:
            return self.stack.pop()
        except IndexError as ie:
            self.logger.exception(ie)
            
    def remove(self, value):
        try:
            self.stack.remove(value)
        except ValueError as ve:
            self.logger.exception(ve)
        
    def isEmpty(self):
        return len(self.stack) == 0

    def top(self):
        if not self.isEmpty():
            return self.stack[-1]
        else:
            return None
