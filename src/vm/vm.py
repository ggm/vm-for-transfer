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

import sys
import logging
from systemstack import SystemStack
from interpreter import Interpreter
from assemblyloader import AssemblyLoader

class VM_STATUS:
    """Represents the state of the vm as a set of constants."""
    RUNNING = 0
    HALTED = 1
    FAILED = 2

class VM:
    """This class encapsulates all the VM processing."""

    def __init__(self):
        self.setUpLogging()
        #Structure of the stores used in the vm.
        self.variables = {}
        self.rulesCode = {}
        self.macrosCode = {}
        self.trie = None

        #Execution state of the vm.
        self.status = VM_STATUS.HALTED

        #Components used by the vm.
        self.stack = SystemStack()
        self.loader = None
        self.interpreter = Interpreter(self)

        #We use 'buffer' to get a stream of bytes, not str.
        self.input = sys.stdin.buffer
        self.output = sys.stdout.buffer

    def setUpLogging(self):
        """Set at least an error through stderr logger"""
        self.formatString = '%(levelname)s: %(filename)s[%(lineno)d]:\t%(message)s'
        self.logger = logging.getLogger('vm')

        errorHandler = logging.StreamHandler(sys.stderr)
        errorHandler.setFormatter(logging.Formatter(self.formatString))
        errorHandler.setLevel(logging.ERROR)
        self.logger.addHandler(errorHandler)

    def setLoader(self, header):
        """Set the loader to use depending on the header of the code file."""

        if "assembly" in header: self.loader = AssemblyLoader()
        else: return False
        return True

    def run(self):
        try:
            pass
        except (Exception) as e:
            self.logger.exception(e)
            exit(1)
