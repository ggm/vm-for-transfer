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

from vm import VM_STATUS
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

    def getWord(self, pos):
        return self.vm.words[self.vm.currentWords[pos - 1]]

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
        self.vm.variables[varName] += string

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
        for op in ops:
            words.append(self.vm.currentWords[op - 1])

        #Create an entry in the call stack with the macro called.
        macroNumber = int(instr[1])
        self.callStack.push("macros", macroNumber, words)
        #Tell the interpreter that the PC has been modified, so it does not.
        self.modifyPC(self.vm.PC)

    def executeRet(self, instr):
        #Restore the last code section and its PC.
        self.callStack.pop()

    def executeClip(self, instr):
        pass

    def executeClipsl(self, instr):
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        word = self.getWord(pos)

        self.handleClipInstruction(parts, word.source)

    def executeCliptl(self, instr):
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        word = self.getWord(pos)

        self.handleClipInstruction(parts, word.target)

    def handleClipInstruction(self, parts, word):
        if parts in ("lem", "lemh", "lemq", "tags"):
            try:
                self.systemStack.push(word.attrs[parts])
            except KeyError:
                self.systemStack.push("")
            return
        elif parts == "whole":
            self.systemStack.push(word.lu)
            return
        else:
            for part in parts.split('|'):
                if part in word.lu:
                    self.systemStack.push(part)
                    return

        #If the word doesn't have the part needed, return "".
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
        name = ops[0]
        tags = ops[1]
        chunk = '^' + name + tags
        if len(ops) > 2:
            chunk += '{'
            for op in ops[2:]: chunk += op
            chunk += '}'
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

        self.systemStack.push(lu)

    def executeLuCount(self, instr):
        pass

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
        pass

    def executeModifyCase(self, instr):
        case = self.systemStack.pop()
        container = self.systemStack.pop()

        if case == "aa": container = container.lower()
        elif case == "Aa": container = container.capitalize()
        elif case == "AA": container = container.upper()

        self.systemStack.push(container)

    def executeOut(self, instr):
        pass

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
                self.raiseError("Variable {} is not defined.".format(varName))

    def executePushbl(self, instr):
        pass

    def executePushsb(self, instr):
        pass

    def executeStorecl(self, instr):
        pass

    def executeStoresl(self, instr):
        value = self.systemStack.pop()
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        word = self.getWord(pos)

        self.handleStoreClipInstruction(parts, word.source, value)

    def executeStoretl(self, instr):
        value = self.systemStack.pop()
        parts = self.systemStack.pop()
        pos = self.systemStack.pop()
        word = self.getWord(pos)

        self.handleStoreClipInstruction(parts, word.target, value)

    def handleStoreClipInstruction(self, parts, word, value):
        if parts in ("lem", "lemh", "lemq", "tags"):
            word.modifyAttr(parts, value)
            return
        else:
            for part in parts.split('|'):
                if part in word.lu:
                    word.modifyTag(part, value)
                    return

        #If the word doesn't have the part needed, return "".
        self.systemStack.push("")

    def executeStorev(self, instr):
        value = self.systemStack.pop()
        varName = self.systemStack.pop()
        self.vm.variables[varName] = value
