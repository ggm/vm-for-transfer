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

from string import capwords

from constants import VM_STATUS, TRANSFER_STAGE
from instructions import OpCodes
from assemblyloader import AssemblyLoader
from interpretererror import InterpreterError

class Interpreter:
    """Interprets an op code and executes the appropriate instruction."""

    def __init__(self, vm):
        #Access to the data structures of the vm is needed.
        self.vm = vm
        self.systemStack = vm.stack
        self.callStack = vm.callStack

        #Record if the last instruction modified the vm's PC.
        self.modifiedPC = False

        #Create a dictionary with the opCode as key and its processing method.
        self.methods = {}
        for attribute in dir(OpCodes):
            if not attribute.startswith("__"):
                opCode = getattr(OpCodes, attribute)
                methodName = "execute"
                methodName += capwords(attribute, '_').replace('_', '')
                self.methods[opCode] = methodName

    def raiseError(self, msg):
        """Raise an error to handle it in the main process."""

        self.vmStatus = VM_STATUS.FAILED
        raise InterpreterError("{}".format(msg))

    def modifyPC(self, newPC):
        """Modify the vm's PC and set it as modified for the interpreter."""

        self.vm.PC = newPC
        self.modifiedPC = True

    def preprocess(self):
        """Execute all the code inside the preprocessing code section."""

        for instr in self.vm.preprocessCode: self.execute(instr)

    def execute(self, instr):
        """Execute a instruction, modifying the vm accordingly."""

        opCode = instr[0]
        methodName = self.methods[opCode]

        if not hasattr(self, methodName):
            self.raiseError("Can't find processing method {} for instruction {}"
                            .format(methodName,
                                    AssemblyLoader.reversedOpCodes[instr[0]]))
        else:
            method = getattr(self, methodName)

        method(instr)

        #If the last instruction didn't modify the PC, point it to the next
        #instruction. In the other case, keep the modified PC.
        if not self.modifiedPC: self.vm.PC += 1
        else: self.modifiedPC = False

    def getNOperands(self, n):
        """Get n operands from the stack and return them reversed."""

        ops = []
        for i in range(n): ops.insert(0, self.systemStack.pop())

        return ops

    def getOperands(self, instr):
        """Get the operands of instr from the stack and return them reversed."""

        numOps = int(instr[1])
        ops = []
        for i in range(numOps): ops.insert(0, self.systemStack.pop())

        return ops

    def getCase(self, string):
        """Get the case of a string, defaulting to capitals."""

        isFirstUpper = string[0].isupper()
        isUpper = string.isupper()

        #If it's a 1-length string and is upper, capitalize it.
        if isUpper and len(string) == 1: return "Aa"
        elif isFirstUpper and not isUpper: return "Aa"
        elif isUpper: return "AA"
        else: return "aa"

    def getSourceLexicalUnit(self, pos):
        """Get a word from the source side for every transfer stage."""

        if self.vm.transferStage == TRANSFER_STAGE.CHUNKER:
            return self.vm.words[self.vm.currentWords[pos - 1]].source
        elif self.vm.transferStage == TRANSFER_STAGE.INTERCHUNK:
            return self.vm.words[self.vm.currentWords[pos - 1]].chunk
        else:
            word = self.vm.words[self.vm.currentWords[0]]

            #If it's a macro, get the position passed as a parameter.
            if len(self.vm.currentWords) > 1: pos = self.vm.currentWords[pos]

            if pos == 0: return word.chunk
            else: return word.content[pos - 1]

    def getTargetLexicalUnit(self, pos):
        """Get a word from the target side only for the chunker stage."""

        return self.vm.words[self.vm.currentWords[pos - 1]].target

    def executeAddtrie(self, instr):
        #Append N number of patterns.
        pattern = []
        numberOfPatterns = self.systemStack.pop()
        while numberOfPatterns > 0:
            pattern.insert(0, self.systemStack.pop().replace("\"", ''))
            numberOfPatterns -= 1

        #Add the pattern with the rule number to the trie. 
        ruleNumber = instr[1]
        self.vm.trie.addPattern(pattern, ruleNumber)

    def executeAnd(self, instr):
        #Get all the operands.
        ops = self.getOperands(instr)

        #Return false (0) if one operand if false.
        for op in ops:
            if op == 0:
                self.systemStack.push(0)
                return
        #Else, return true (1).
        self.systemStack.push(1)

    def executeOr(self, instr):
        #Get all the operands.
        ops = self.getOperands(instr)

        #Return true (1) if one operand if true.
        for op in ops:
            if op == 1:
                self.systemStack.push(1)
                return
        #Else, return false (0).
        self.systemStack.push(0)

    def executeNot(self, instr):
        op1 = self.systemStack.pop()

        if op1 == 0: self.systemStack.push(1)
        elif op1 == 1: self.systemStack.push(0)

    def executeAppend(self, instr):
        ops = self.getOperands(instr)
        string = ""
        for op in ops: string += op

        varName = self.systemStack.pop()
        self.vm.variables[varName] = self.vm.variables[varName] + string

    def executeBeginsWith(self, instr):
        prefixes = self.systemStack.pop()
        word = self.systemStack.pop()

        for prefix in prefixes.split("|"):
            if word.startswith(prefix):
                self.systemStack.push(1)
                return

        self.systemStack.push(0)

    def executeBeginsWithIg(self, instr):
        prefixes = self.systemStack.pop()
        word = self.systemStack.pop().lower()

        for prefix in prefixes.split("|"):
            if word.startswith(prefix.lower()):
                self.systemStack.push(1)
                return

        self.systemStack.push(0)

    def executeCall(self, instr):
        #Save current PC to return later when the macro ends.
        self.callStack.saveCurrentPC()

        #Get the words passed as argument to the macro.
        ops = self.getNOperands(self.systemStack.pop())
        words = []

        #For the postchunk append the index of the only current word and then
        #append all the parameters.
        if self.vm.transferStage == TRANSFER_STAGE.POSTCHUNK:
            words.append(self.vm.currentWords[0])
            for op in ops: words.append(op)
        #For the rest, just append the index of the current words.
        else:
            for op in ops: words.append(self.vm.currentWords[op - 1])

        #Create an entry in the call stack with the macro called.
        macroNumber = int(instr[1])
        self.callStack.push("macros", macroNumber, words)
        #Tell the interpreter that the PC has been modified, so it does not.
        self.modifyPC(self.vm.PC)

    def executeRet(self, instr):
        #Restore the last code section and its PC.
        self.callStack.pop()

    def executeClip(self, instr):
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        lu = self.getSourceLexicalUnit(pos)

        if len(instr) > 1: linkTo = str(instr[1].replace('"', ''))
        else: linkTo = None

        lemmaAndTags = lu.attrs['lem'] + lu.attrs['tags']
        self.handleClipInstruction(parts, lu, lemmaAndTags, linkTo)

    def executeClipsl(self, instr):
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        lu = self.getSourceLexicalUnit(pos)

        if len(instr) > 1: linkTo = str(instr[1].replace('"', ''))
        else: linkTo = None

        self.handleClipInstruction(parts, lu, lu.lu, linkTo)

    def executeCliptl(self, instr):
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        lu = self.getTargetLexicalUnit(pos)

        if len(instr) > 1: linkTo = str(instr[1].replace('"', ''))
        else: linkTo = None

        self.handleClipInstruction(parts, lu, lu.lu, linkTo)

    def handleClipInstruction(self, parts, lu, lemmaAndTags, linkTo):
        if linkTo is None and parts in ("lem", "lemh", "lemq", "tags", "chcontent"):
            try:
                self.systemStack.push(lu.attrs[parts])
            except KeyError:
                self.systemStack.push("")
            return
        elif linkTo is None and parts == "whole":
            self.systemStack.push(lu.lu)
            return
        else:
            longestMatch = ""
            for part in parts.split('|'):
                if part in lemmaAndTags:
                    if linkTo:
                        self.systemStack.push(linkTo)
                        return
                    else:
                        if len(part) > len(longestMatch): longestMatch = part
            if longestMatch:
                self.systemStack.push(longestMatch)
                return

        #If the lu doesn't have the part needed, return "".
        self.systemStack.push("")

    def executeCmp(self, instr):
        op1 = self.systemStack.pop()
        op2 = self.systemStack.pop()

        if op1 == op2: self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeCmpi(self, instr):
        op1 = self.systemStack.pop()
        op2 = self.systemStack.pop()

        if op1.lower() == op2.lower(): self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeCmpSubstr(self, instr):
        op1 = self.systemStack.pop()
        op2 = self.systemStack.pop()

        if op1 in op2: self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeCmpiSubstr(self, instr):
        op1 = self.systemStack.pop()
        op2 = self.systemStack.pop()

        if op1.lower() in op2.lower(): self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeIn(self, instr):
        list = self.systemStack.pop()
        list = list.split('|')
        value = self.systemStack.pop()

        if value in list: self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeInig(self, instr):
        list = self.systemStack.pop()
        list = list.split('|')
        list = [w.lower() for w in list]

        value = self.systemStack.pop()
        value = value.lower()

        if value in list: self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeConcat(self, instr):
        ops = self.getOperands(instr)
        string = ""
        for op in ops: string += op

        self.systemStack.push(string)

    def executeChunk(self, instr):
        ops = self.getOperands(instr)

        #If there is only one operand it's the full content of the chunk.
        if len(ops) == 1:
            chunk = '^' + ops[0] + '$'
        else:
            name = ops[0]
            tags = ops[1]
            chunk = '^' + name + tags
            if len(ops) > 2:
                #Only output enclosing {} in the chunker, in the interchunk the
                #'chcontent' will already have the {}.
                if self.vm.transferStage == TRANSFER_STAGE.CHUNKER: chunk += '{'
                for op in ops[2:]: chunk += op
                if self.vm.transferStage == TRANSFER_STAGE.CHUNKER: chunk += '}'
            chunk += '$'

        self.systemStack.push(chunk)

    def executeEndsWith(self, instr):
        suffixes = self.systemStack.pop()
        word = self.systemStack.pop()

        for suffix in suffixes.split("|"):
            if word.endswith(suffix):
                self.systemStack.push(1)
                return

        self.systemStack.push(0)

    def executeEndsWithIg(self, instr):
        suffixes = self.systemStack.pop()
        word = self.systemStack.pop().lower()

        for suffix in suffixes.split("|"):
            if word.endswith(suffix.lower()):
                self.systemStack.push(1)
                return

        self.systemStack.push(0)

    def executeJmp(self, instr):
        jumpTo = int(instr[1])
        self.modifyPC(jumpTo)

    def executeJz(self, instr):
        condition = self.systemStack.pop()
        if condition == 0:
            jumpTo = int(instr[1])
            self.modifyPC(jumpTo)

    def executeJnz(self, instr):
        condition = self.systemStack.pop()
        if condition != 0:
            jumpTo = int(instr[1])
            self.modifyPC(jumpTo)

    def executeLu(self, instr):
        ops = self.getOperands(instr)

        lu = "^"
        for op in ops: lu += op
        lu += "$"

        #If the lu is empty, only the ^$, then push an empty string.
        if len(lu) == 2: self.systemStack.push("")
        else: self.systemStack.push(lu)

    def executeLuCount(self, instr):
        chunk = self.vm.words[self.vm.currentWords[0]]
        self.systemStack.push(len(chunk.content))

    def executeMlu(self, instr):
        ops = self.getOperands(instr)

        #Append the lexical units, removing its ^...$
        mlu = "^" + ops[0][1:-1]
        for op in ops[1:]: mlu += "+" + op[1:-1]
        mlu += "$"

        self.systemStack.push(mlu)

    def executeCaseOf(self, instr):
        value = self.systemStack.pop()
        case = self.getCase(value)
        self.systemStack.push(case)

    def executeGetCaseFrom(self, instr):
        pos = self.systemStack.pop()
        lu = self.getSourceLexicalUnit(pos)
        lem = lu.attrs['lem']

        case = self.getCase(lem)
        self.systemStack.push(case)

    def executeModifyCase(self, instr):
        case = self.systemStack.pop()
        container = self.systemStack.pop()

        if container != "":
            if case == "aa": container = container.lower()
            elif case == "Aa": container = container[0].upper() + container[1:]
            elif case == "AA": container = container.upper()

        self.systemStack.push(container)

    def executeOut(self, instr):
        ops = self.getOperands(instr)
        out = ""
        for op in ops: out += op
        self.vm.writeOutput(out)

    def executePush(self, instr):
        #If it's a string, push it without quotes.
        if '"' in instr[1]: self.systemStack.push(instr[1].replace('"', ''))
        #Push strings containing numbers as int.
        elif instr[1].isnumeric(): self.systemStack.push(int(instr[1]))
        #If it's a variable reference, eval it and push the value.
        else:
            varName = instr[1]
            try:
                self.systemStack.push(self.vm.variables[varName])
            except:
                self.vm.variables[varName] = ""
                self.systemStack.push("")

    def executePushbl(self, instr):
        self.systemStack.push(" ")

    def executePushsb(self, instr):
        #The position is relative to the current word(s), so we have to get the
        #actual one. For the postchunk, the relative is the actual one because
        #each chunk stores the blanks in their content.
        relativePos = int(instr[1])

        try:
            if self.vm.transferStage == TRANSFER_STAGE.POSTCHUNK:
                word = self.vm.words[self.vm.currentWords[0]]
                self.systemStack.push(word.blanks[relativePos])
            else:
                actualPos = relativePos + self.vm.currentWords[0]
                self.systemStack.push(self.vm.superblanks[actualPos])
        except:
            self.systemStack.push("")

    def executeStorecl(self, instr):
        value = self.systemStack.pop()
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        lu = self.getSourceLexicalUnit(pos)

        lemmaAndTags = lu.attrs['lem'] + lu.attrs['tags']
        self.handleStoreClipInstruction(parts, lu, lemmaAndTags, value)

    def executeStoresl(self, instr):
        value = self.systemStack.pop()
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        lu = self.getSourceLexicalUnit(pos)

        self.handleStoreClipInstruction(parts, lu, lu.lu, value)

    def executeStoretl(self, instr):
        value = self.systemStack.pop()
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        lu = self.getTargetLexicalUnit(pos)

        self.handleStoreClipInstruction(parts, lu, lu.lu, value)

    def handleStoreClipInstruction(self, parts, lu, lemmaAndTags, value):
        oldLu = lu.lu
        change = False

        if parts in ('lem', 'lemh', 'lemq', 'tags'):
            lu.modifyAttr(parts, value)
            change = True
        elif parts == 'chcontent':
            lu.modifyAttr(parts, value)
            if self.vm.transferStage == TRANSFER_STAGE.POSTCHUNK:
                #If we are in the postchunk stage and change the chunk content
                #we need to parse it again, so we can use it as lexical units.
                chunkWord = self.vm.words[self.vm.currentWords[0]]
                chunkWord.parseChunkContent()
        elif parts == 'whole':
            lu.modifyAttr(parts, value)
            change = True
        else:
            longestMatch = ""
            for part in parts.split('|'):
                if part in lemmaAndTags:
                    if len(part) > len(longestMatch): longestMatch = part
            if longestMatch:
                lu.modifyTag(longestMatch, value)
                change = True

        if change and self.vm.transferStage == TRANSFER_STAGE.POSTCHUNK:
            #Update the chunk content when changing a lu inside the chunk.
            chunkWord = self.vm.words[self.vm.currentWords[0]]
            chunkWord.updateChunkContent(oldLu, lu.lu)

    def executeStorev(self, instr):
        value = self.systemStack.pop()
        varName = self.systemStack.pop()
        self.vm.variables[varName] = value
