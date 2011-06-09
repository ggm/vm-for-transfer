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
from compilererror import CompilerError

class Compiler:
    """This class encapsulates all the compiling process."""
    
    def __init__(self):
        self.setUpLogging()
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
        self.eventHandler = EventHandler(self)
        self.parser = ExpatParser(self)

    def setUpLogging(self):
        """Set at least an error through stderr logger"""
        self.formatString = '%(levelname)s: %(filename)s[%(lineno)d]:\t%(message)s'
        self.logger = logging.getLogger('compiler')

        errorHandler = logging.StreamHandler(sys.stderr)
        errorHandler.setFormatter(logging.Formatter(self.formatString))
        errorHandler.setLevel(logging.ERROR)
        self.logger.addHandler(errorHandler)

    def setDebug(self, fileName):
        """Set the debug capabilities using the file passed."""
        self.debug = True
        self.codeGenerator.debug = True
        self.logger.setLevel(logging.DEBUG)
        
        debugHandler = logging.FileHandler(filename=fileName, mode='w', encoding='utf-8')
        debugHandler.setFormatter(logging.Formatter(self.formatString))
        debugHandler.setLevel(logging.DEBUG)
        self.logger.addHandler(debugHandler)

    def compile(self):
        try:
            self.parser.parse(self.input.read())
            self.output.write(self.codeGenerator.getWritableCode())
            self.logger.debug(str(self.symbolTable))
        except (CompilerError, Exception) as e:
            if self.debug: self.logger.exception(e)
            else: self.logger.error(e)
            exit(1)
