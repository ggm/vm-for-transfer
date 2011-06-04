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
from assemblycodegenerator import AssemblyCodeGenerator
from symboltable import SymbolTable

class Compiler:
    """This class encapsulates all the compiling process."""
    
    def __init__(self):
        self.logger = logging.getLogger('compiler')
        self.logger.setLevel(logging.INFO)
        self.debug = False
        
        #We use 'buffer' to get a stream of bytes, not str.
        self.input = sys.stdin.buffer
        self.output = sys.stdout.buffer
        
        #Create all the data structures needed.
        self.defCats = {}
        self.defAttrs = {}
        self.defVars = {}
        self.defLists = {}
        
        #Initialize all the compiler's components.
        self.callStack = CallStack()
        self.symbolTable = SymbolTable()
        self.codeGenerator = AssemblyCodeGenerator()    #here we set the code generator to use
        self.eventHandler = EventHandler(self, self.codeGenerator, self.symbolTable)
        self.parser = ExpatParser(self)

    def setDebug(self, fileName):
        """Set the debug capabilities and configure it with a custom format."""
        formatString = '%(levelname)s: %(filename)s[%(lineno)d]:\t%(message)s'
        logging.basicConfig(filename=fileName, format=formatString)
        self.debug = True
        self.codeGenerator.debug = True
        self.logger.setLevel(logging.DEBUG)
        
    def compile(self):
        self.parser.parse(self.input.read())
        self.output.write('\n'.join(self.codeGenerator.code).encode('utf-8'))
        self.logger.debug(str(self.symbolTable))
