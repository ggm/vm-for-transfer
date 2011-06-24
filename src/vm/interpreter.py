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

    def executeAddtrie(self, instr):
        pass

    def executeAnd(self, instr):
        pass

    def executeAppend(self, instr):
        pass

    def executeBeginsWith(self, instr):
        pass

    def executeBeginsWithIg(self, instr):
        pass

    def executeCall(self, instr):
        pass

    def executeClip(self, instr):
        pass

    def executeClipsl(self, instr):
        pass

    def executeCliptl(self, instr):
        pass

    def executeCmp(self, instr):
        pass

    def executeCmpi(self, instr):
        pass

    def executeCmpSubstr(self, instr):
        pass

    def executeCmpiSubstr(self, instr):
        pass

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

    def executeIn(self, instr):
        pass

    def executeInig(self, instr):
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

    def executeNot(self, instr):
        pass

    def executeOr(self, instr):
        pass

    def executeOut(self, instr):
        pass

    def executePush(self, instr):
        self.systemStack.push(instr[1])

    def executePushbl(self, instr):
        pass

    def executePushsb(self, instr):
        pass

    def executeRet(self, instr):
        pass

    def executeStorecl(self, instr):
        pass

    def executeStoresl(self, instr):
        pass

    def executeStoretl(self, instr):
        pass

    def executeStorev(self, instr):
        pass
