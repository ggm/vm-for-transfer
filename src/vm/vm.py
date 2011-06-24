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
from assemblyloader import AssemblyLoader
from systemtrie import SystemTrie
from transferword import TransferWordTokenizer

class VM_STATUS:
    """Represents the state of the vm as a set of constants."""
    RUNNING = 0
    HALTED = 1
    FAILED = 2

from interpreter import Interpreter

class VM:
    """This class encapsulates all the VM processing."""

    def __init__(self):
        self.setUpLogging()

        #Program counter: position of the next instruction to execute.
        self.PC = 0

        #Structure of the stores used in the vm.
        self.variables = {}
        self.code = []
        self.rulesCode = []
        self.macrosCode = []
        self.preprocessCode = []
        self.trie = SystemTrie()

        #Current code section in execution (a macro, a rule, ...).
        self.currentCodeSection = self.code

        #Execution state of the vm.
        self.status = VM_STATUS.HALTED

        #Input will be divided in words with their patterns information.
        self.words = []
        self.nextPattern = -1

        #Components used by the vm.
        self.stack = SystemStack()
        self.loader = None
        self.interpreter = Interpreter(self)

        self.input = sys.stdin
        #We use 'buffer' to get a stream of bytes, not str, because we want to
        #encode it using utf-8 (just for safety).
        self.output = sys.stdout.buffer

    def setUpLogging(self):
        """Set at least an error through stderr logger"""

        self.formatStr = '%(levelname)s: %(filename)s[%(lineno)d]:\t%(message)s'
        self.logger = logging.getLogger('vm')

        errorHandler = logging.StreamHandler(sys.stderr)
        errorHandler.setFormatter(logging.Formatter(self.formatStr))
        errorHandler.setLevel(logging.ERROR)
        self.logger.addHandler(errorHandler)

    def setLoader(self, header, t1xFile):
        """Set the loader to use depending on the header of the code file."""

        if "assembly" in header: self.loader = AssemblyLoader(self, t1xFile)
        else: return False
        return True

    def tokenizeInput(self):
        """Call to the tokenizer to divide the input in tokens."""

        tokenizer = TransferWordTokenizer()
        self.words = tokenizer.tokenize(self.input)

    def getNextInputPattern(self):
        """Get the next input pattern to analyse."""

        self.nextPattern += 1
        try:
            return self.words[self.nextPattern].source
        except IndexError:
            return None

    def initializeVM(self):
        """Execute code to initialize the VM, e.g. default values for vars."""

        self.PC = 0
        self.status = VM_STATUS.RUNNING
        while self.status == VM_STATUS.RUNNING and self.PC < len(self.code):
            self.interpreter.execute(self.code[self.PC])

    def run(self):
        """Load, preprocess and execute the contents of the files."""

        try:
            self.loader.load()
            self.interpreter.preprocess()
            self.initializeVM()
            self.tokenizeInput()

            pattern = self.getNextInputPattern()
            while pattern and self.status == VM_STATUS.RUNNING:
                print(pattern)
                pattern = self.getNextInputPattern()

            self.printCodeSections()
        except (Exception) as e:
            self.logger.exception(e)
            exit(1)

    def printCodeSections(self):
        """Print all the code sections for information or debugging purposes."""

        self.printSection(self.code, "Code")
        self.printSection(self.preprocessCode, "Preprocess")
        self.printSection(self.rulesCode, "Rules", enum=True)
        self.printSection(self.macrosCode, "Macros", enum=True)

    def printSection(self, section, headerText, enum=False):
        """Print a code section for information or debugging purposes."""

        symbol = '='
        header = symbol * 20 + " {:=<39}"
        footer = symbol * 60 + '\n'
        opCodes = self.loader.reversedOpCodes

        if not enum:
            print(header.format(headerText + " section "))
            for number, code in enumerate(section):
                if len(code) > 1: print(number, opCodes[int(code[0])], code[1])
                else: print(number, opCodes[code[0]])
        else:
            print(header.format(headerText + " code section "))
            for number, code in enumerate(section):
                print("\n{} {}:".format(headerText[:-1], number))
                for v, c in enumerate(code):
                    if len(c) > 1: print(v, opCodes[int(c[0])], c[1])
                    else: print(v, opCodes[c[0]])

        print(footer)
