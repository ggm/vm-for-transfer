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

from constants import VM_STATUS, TRANSFER_STAGE, CHUNKER_MODE
from systemstack import SystemStack
from assemblyloader import AssemblyLoader
from interpreter import Interpreter
from systemtrie import SystemTrie
from transferword import TransferWordTokenizer
from transferword import ChunkWordTokenizer
from callstack import CallStack
from debugger import Debugger

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
        self.lastSuperblank = -1
        self.currentWords = []
        self.nextPattern = 0

        #Components used by the vm.
        self.tokenizer = None
        self.callStack = CallStack(self)
        self.stack = SystemStack()
        self.loader = None
        self.interpreter = Interpreter(self)

        #Components used only in debug mode.
        self.debugger = None
        self.debugMode = False

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

    def setDebugMode(self):
        """Set the debug mode, creating a debugger an setting it up as a proxy."""
        self.debugMode = True
        self.debugger = Debugger(self, self.interpreter)
        #Set the debugger as a proxy.
        self.interpreter = self.debugger

        #Create a logging handler for debugging messages.
        debugHandler = logging.StreamHandler(sys.stdout)
        debugHandler.setFormatter(logging.Formatter(self.formatStr))
        debugHandler.setLevel(logging.DEBUG)
        self.logger.addHandler(debugHandler)

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
            self.tokenizer = ChunkWordTokenizer(solveRefs=True,
                                                parseContent=True)

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
        """Get the part of a source word needed for pattern matching, depending
           on the transfer stage."""

        if self.transferStage == TRANSFER_STAGE.CHUNKER:
            return self.words[pos].source.lu
        elif self.transferStage == TRANSFER_STAGE.INTERCHUNK:
            word = self.words[pos].chunk
            return word.attrs['lem'] + word.attrs['tags']
        else:
            return self.words[pos].chunk.attrs['lem']

    def getNextInputPattern(self):
        """Get the next input pattern to analyze, lowering the lemma first."""

        try:
            pattern = self.getSourceWord(self.nextPattern)
            tag = pattern.find('<')
            pattern = pattern[:tag].lower() + pattern[tag:]
            self.nextPattern += 1
        except IndexError:
            return None

        return pattern

    def getUniqueSuperblank(self, pos):
        """Get the superblank at pos avoiding duplicates."""

        try:
            if pos != self.lastSuperblank:
                self.lastSuperblank = pos
                return self.superblanks[pos]
        except IndexError:
            pass

        return ""

    def selectNextRule(self):
        """Select the next rule to execute depending on the transfer stage."""

        if self.transferStage == TRANSFER_STAGE.POSTCHUNK:
            self.selectNextRulePostChunk()
        else: self.selectNextRuleLRLM()


    def selectNextRulePostChunk(self):
        """Select the next rule trying to match patterns one by one."""

        #Go through all the patterns until one matches a rule.
        while self.nextPattern < len(self.words):
            startPatternPos = self.nextPattern
            pattern = self.getNextInputPattern()
            ruleNumber = self.trie.getRuleNumber(pattern)
            if ruleNumber is not None:
#                print('Pattern "{}" match rule: {}'.format(pattern, ruleNumber))
                self.setRuleSelected(ruleNumber, startPatternPos, pattern)
                return
            else:
                self.processUnmatchedPattern(self.words[startPatternPos])

        #if there isn't any rule at all to execute, stop the vm.
        self.status = VM_STATUS.HALTED

    def selectNextRuleLRLM(self):
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
                end = fullPattern.find(self.getSourceWord(self.nextPattern))
                if end > 0: fullPattern = fullPattern[:end]

            #If there is a longest match, set the rule to process
            if longestMatch is not None:
#                print('Pattern "{}" match rule: {}'.format(fullPattern, longestMatch))
                self.setRuleSelected(longestMatch, startPatternPos, fullPattern)
                return
            #Otherwise, process the unmatched pattern.
            else: self.processUnmatchedPattern(self.words[self.nextPattern - 1])

            longestMatch = None

        #if there isn't any rule at all to execute, stop the vm.
        self.status = VM_STATUS.HALTED

    def setRuleSelected(self, ruleNumber, startPos, pattern):
        """Set a rule and its words as current ones."""

        #Output the leading superblank of the matched pattern.
        self.writeOutput(self.getUniqueSuperblank(startPos))

        #Add only a reference to the index pos of words, to avoid copying them.
        wordsIndex = []
        while startPos != self.nextPattern:
            wordsIndex.append(startPos)
            startPos += 1

        #Create an entry in the call stack with the rule to execute.
        self.callStack.push("rules", ruleNumber, wordsIndex)

        if self.debugMode: self.debugger.ruleSelected(pattern, ruleNumber)

    def processRuleEnd(self):
        """Do all the processing needed when rule ends."""

        #Output the trailing superblank of the matched pattern.
        self.writeOutput(self.getUniqueSuperblank(self.nextPattern))

    def processUnmatchedPattern(self, word):
        """Output unmatched patterns as the default form."""
        default = ""

        #Output the leading superblank of the unmatched pattern.
        default += self.getUniqueSuperblank(self.nextPattern - 1)

        #For the chunker, output the default version of the unmatched pattern.
        if self.transferStage == TRANSFER_STAGE.CHUNKER:
            #If the target word is empty, we don't need to output anything.
            if word.target.lu != "":
                wordTL = '^' + word.target.lu + '$'
                if self.chunkerMode == CHUNKER_MODE.CHUNK:
                    if wordTL[1] == '*': default += "^unknown<unknown>{" + wordTL + "}$"
                    else: default += "^default<default>{" + wordTL + "}$"
                else:
                    default += wordTL

        #For the interchunk stage only need to output the complete chunk.
        elif self.transferStage == TRANSFER_STAGE.INTERCHUNK:
            default += '^' + word.chunk.lu + '$'

        #Lastly, for the postchunk stage output the lexical units inside chunks
        #with the case of the chunk pseudolemma.
        else:
            default += word.chunk.attrs['chcontent'][1:-1]

        #Output the trailing superblank of the matched pattern.
        default += self.getUniqueSuperblank(self.nextPattern)

        self.writeOutput(default)

    def terminateVM(self):
        """Do all the processing needed when the vm is being turned off."""

        pass

    def writeOutput(self, string):
        """A single entry point to write strings to the output."""

        self.output.write(string.encode("utf-8"))

    def run(self):
        """Load, preprocess and execute the contents of the files."""

        try:
            self.loader.load()
            self.interpreter.preprocess()
            self.initializeVM()
            self.tokenizeInput()

            if self.debugMode: self.debugger.start()

            #Select the first rule. If there isn't one, the vm work has ended.
            if self.status == VM_STATUS.RUNNING: self.selectNextRule()
            while self.status == VM_STATUS.RUNNING:
                #Execute the rule selected until it ends.
                while self.status == VM_STATUS.RUNNING and self.PC < self.endAddress:
                    self.interpreter.execute(self.currentCodeSection[self.PC])

                self.processRuleEnd()
                #Select the next rule to execute.
                if self.status == VM_STATUS.RUNNING: self.selectNextRule()

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

