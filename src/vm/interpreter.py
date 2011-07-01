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

    def getOperands(self, instr):
        """Get n operands from the stack and return them reversed."""

        numOps = int(instr[1])
        ops = []
        for i in range(numOps): ops.insert(0, self.systemStack.pop())

        return ops

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
        pass

    def executeBeginsWithIg(self, instr):
        pass

    def executeCall(self, instr):
        #Save current PC to return later when the macro ends.
        self.callStack.saveCurrentPC()

        #Create an entry in the call stack with the macro called.
        macroNumber = int(instr[1])
        self.callStack.push("macros", macroNumber)

    def executeRet(self, instr):
        #Restore the last code section and its PC.
        self.callStack.pop()

    def executeClip(self, instr):
        pass

    def executeClipsl(self, instr):
        pass

    def executeCliptl(self, instr):
        pass

    def executeCmp(self, instr):
        op1 = self.systemStack.pop()
        op2 = self.systemStack.pop()

        if op1 == op2: self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeCmpi(self, instr):
        op1 = str(self.systemStack.pop())
        op2 = str(self.systemStack.pop())

        if op1.lower() == op2.lower(): self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeCmpSubstr(self, instr):
        op1 = self.systemStack.pop()
        op2 = self.systemStack.pop()

        if op1 in op2: self.systemStack.push(1)
        else: self.systemStack.push(0)

    def executeCmpiSubstr(self, instr):
        op1 = str(self.systemStack.pop())
        op2 = str(self.systemStack.pop())

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
        pass

    def executeChunk(self, instr):
        pass

    def executeEndsWith(self, instr):
        pass

    def executeEndsWithIg(self, instr):
        pass

    def executeGetCaseFrom(self, instr):
        pass

    def executeJmp(self, instr):
        jumpTo = int(instr[1])
        self.modifyPC(jumpTo)

    def executeJz(self, instr):
        pass

    def executeJnz(self, instr):
        pass

    def executeLu(self, instr):
        pass

    def executeLuCount(self, instr):
        pass

    def executeMlu(self, instr):
        pass

    def executeModifyCase(self, instr):
        pass

    def executeOut(self, instr):
        pass

    def executePush(self, instr):
        #If it's a string, push it without quotes.
        if '"' in instr[1]: self.systemStack.push(instr[1].replace('"', ''))
        #Push strings containing numbers as int.
        elif instr[1].isnumeric(): self.systemStack.push(int(instr[1]))
        #If it's a variable reference, eval it and push the value.
        elif instr[1].isalpha():
            varName = instr[1]
            try:
                self.systemStack.push(self.vm.variables[varName])
            except:
                self.raiseError("Variable {} is not defined.".format(varName))
        #If it's another thing push it as it comes.
        else: self.systemStack.push(instr[1])

    def executePushbl(self, instr):
        pass

    def executePushsb(self, instr):
        pass

    def executeStorecl(self, instr):
        pass

    def executeStoresl(self, instr):
        pass

    def executeStoretl(self, instr):
        pass

    def executeStorev(self, instr):
        value = self.systemStack.pop()
        varName = self.systemStack.pop()
        self.vm.variables[varName] = value
