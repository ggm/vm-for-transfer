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
from transferword import ChunkWordTokenizer
from callstack import CallStack

class VM_STATUS:
    """Represents the state of the vm as a set of constants."""

    RUNNING = 0
    HALTED = 1
    FAILED = 2

class TRANSFER_STAGE:
    """Represents the current stage of the transfer system."""

    CHUNKER = 0
    INTERCHUNK = 1
    POSTCHUNK = 2

class CHUNKER_MODE:
    """Represents the default behavior in the chunker stage."""

    CHUNK = 0
    LU = 1

from interpreter import Interpreter

class VM:
    """This class encapsulates all the VM processing."""

    def __init__(self):
        self.setUpLogging()

        #Program counter: position of the next instruction to execute.
        self.PC = 0
        self.endAddress = 0

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

        #Transfer stage (chunker, interchunk or postchunk).
        self.transferStage = None
        #Chunker mode to process in shallow mode or advanced transfer.
        self.chunkerMode = None

        #Input will be divided in words with their patterns information.
        self.words = []
        self.superblanks = []
        self.currentWords = []
        self.nextPattern = 0

        #Components used by the vm.
        self.tokenizer = None
        self.callStack = CallStack(self)
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

    def setTransferStage(self, transferHeader):
        """Set the transfer stage to process by the vm."""

        if "transfer" in transferHeader:
            self.transferStage = TRANSFER_STAGE.CHUNKER
            self.tokenizer = TransferWordTokenizer()
            #Set chunker mode, by default 'lu'.
            if "chunk" in transferHeader: self.chunkerMode = CHUNKER_MODE.CHUNK
            else: self.chunkerMode = CHUNKER_MODE.LU
        elif "interchunk" in transferHeader:
            self.transferStage = TRANSFER_STAGE.INTERCHUNK
            self.tokenizer = ChunkWordTokenizer()
        elif "postchunk" in transferHeader:
            self.transferStage = TRANSFER_STAGE.POSTCHUNK
            self.tokenizer = ChunkWordTokenizer()

    def tokenizeInput(self):
        """Call to the tokenizer to divide the input in tokens."""

        self.words, self.superblanks = self.tokenizer.tokenize(self.input)

    def initializeVM(self):
        """Execute code to initialize the VM, e.g. default values for vars."""

        self.PC = 0
        self.status = VM_STATUS.RUNNING
        while self.status == VM_STATUS.RUNNING and self.PC < len(self.code):
            self.interpreter.execute(self.code[self.PC])

    def getSourceWord(self, pos):
        if self.transferStage == TRANSFER_STAGE.CHUNKER:
                return self.words[self.nextPattern].source
        else: return self.words[self.nextPattern].chunk

    def getNextInputPattern(self):
        """Get the next input pattern to analyse."""

        try:
            pattern = self.getSourceWord(self.nextPattern).lu
            self.nextPattern += 1
        except IndexError:
            return None

        return pattern

    def selectNextRule(self):
        """Select the next rule to execute matching the LRLM pattern."""

        longestMatch = None
        nextPatternToProcess = self.nextPattern

        #Go through all the patterns until one matches a rule.
        while self.nextPattern < len(self.words):
            startPatternPos = self.nextPattern
            #Get the next pattern to process
            pattern = self.getNextInputPattern()
            curNodes = self.trie.getPatternNodes(pattern)
            nextPatternToProcess += 1

            #Get the longest match, left to right
            fullPattern = pattern
            while len(curNodes) > 0:
                #Update the longest match if needed.
                ruleNumber = self.trie.getRuleNumber(fullPattern)
                if ruleNumber is not None:
                    longestMatch = ruleNumber
                    nextPatternToProcess = self.nextPattern

                #Continue trying to match current pattern + the next one.
                pattern = self.getNextInputPattern()
                if pattern: fullPattern += pattern 
                nextNodes = []
                for node in curNodes:
                    nextNodes.extend(self.trie.getPatternNodes(pattern, node))
                curNodes = nextNodes

            #If the pattern doesn't match, we will continue with the next one.
            #If there is a match of a group of patterns, we will continue with
            #the last unmatched pattern.
            self.nextPattern = nextPatternToProcess

            #Get the full pattern matched by the rule.
            if self.nextPattern < len(self.words):
                end = fullPattern.find(self.getSourceWord(self.nextPattern).lu)
                if end > 0: fullPattern = fullPattern[:end]

            #If there is a longest match, set the rule to process
            if longestMatch is not None:
                print('Pattern "{}" match rule: {}'.format(fullPattern, longestMatch))
                self.setRuleSelected(longestMatch, startPatternPos)
                return
            #Otherwise, process the unmatched pattern.
            else: self.processUnmatchedPattern(self.words[self.nextPattern - 1])

            longestMatch = None

        #if there isn't any rule at all to execute, stop the vm.
        self.status = VM_STATUS.HALTED

    def setRuleSelected(self, ruleNumber, startPos):
        """Set a rule and its words as current ones."""

        #Add only a reference to the index pos of words, to avoid copying them.
        wordsIndex = []
        while startPos != self.nextPattern:
            wordsIndex.append(startPos)
            startPos += 1

        #Create an entry in the call stack with the rule to execute.
        self.callStack.push("rules", ruleNumber, wordsIndex)

    def processUnmatchedPattern(self, word):
        """Output unmatched patterns as the default form."""

        #If it isn't the first pattern print a blank.
        if self.nextPattern != 1: default = " "
        else: default = ""

        #Output the default version of the unmatched pattern.
        wordTL = '^' + word.target.lu + '$'
        if self.chunkerMode == CHUNKER_MODE.CHUNK:
            if wordTL[1] == '*': default += "^unknown<unknown>{" + wordTL + "}$"
            else: default += "^default<default>{" + wordTL + "}$"
        else:
            default += wordTL
        self.output.write(default.encode("utf-8"))

    def terminateVM(self):
        """Do all the processing needed when the vm is being turned off."""

        if self.status != VM_STATUS.FAILED:
            self.output.write('\n'.encode("utf-8"))

    def run(self):
        """Load, preprocess and execute the contents of the files."""

        try:
            self.loader.load()
            self.interpreter.preprocess()
            self.initializeVM()
            self.tokenizeInput()
#            self.printCodeSections()

            #Select the first rule, if there isn't one, the vm work has ended.
            self.selectNextRule()
            while self.status == VM_STATUS.RUNNING:
                #Execute the rule selected until it ends.
                while self.status == VM_STATUS.RUNNING and self.PC < self.endAddress:
                    self.interpreter.execute(self.currentCodeSection[self.PC])

                #If the vm executed correctly the rule we can continue.
                if self.status == VM_STATUS.HALTED:
                    self.status = VM_STATUS.RUNNING

                #Select the next rule to execute.
                self.selectNextRule()

        except (Exception) as e:
            self.logger.exception(e)
            exit(1)

        self.terminateVM()

    def printCodeSections(self):
        """Print all the code sections for information or debugging purposes."""

        self.loader.printSection(self.code, "Code")
        self.loader.printSection(self.preprocessCode, "Preprocess")
        self.loader.printSection(self.rulesCode, "Rules", enum=True)
        self.loader.printSection(self.macrosCode, "Macros", enum=True)

