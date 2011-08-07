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
from loadererror import LoaderError
from scope import Scope
from instructions import OpCodes

class AssemblyLoader:
    """
    Reads and loads assembly instruction from a file and converts them to
    the format used by the VM.
    """

    #Assembly to vm internal representation table. We could create a dictionary
    #from an enumerated list but it's better to keep it the more static we can.
    #This way it's easier to check the values and tests when maintaining it.
    opCodes = {
               "addtrie" : OpCodes.ADDTRIE, "and" : OpCodes.AND,
               "append" : OpCodes.APPEND, "begins-with" : OpCodes.BEGINS_WITH,
               "begins-with-ig" : OpCodes.BEGINS_WITH_IG, "or" : OpCodes.OR,
               "call" : OpCodes.CALL, "cmp-substr": OpCodes.CMP_SUBSTR,
               "cmpi-substr" : OpCodes.CMPI_SUBSTR, "clip" : OpCodes.CLIP,
               "clipsl" : OpCodes.CLIPSL, "cliptl" : OpCodes.CLIPTL,
               "cmp" : OpCodes.CMP, "cmpi" : OpCodes.CMPI,
               "concat" : OpCodes.CONCAT, "chunk" : OpCodes.CHUNK,
               "ends-with" : OpCodes.ENDS_WITH,
               "ends-with-ig" : OpCodes.ENDS_WITH_IG,
               "get-case-from" : OpCodes.GET_CASE_FROM,
               "in" : OpCodes.IN, "inig" : OpCodes.INIG, "jmp" : OpCodes.JMP,
               "jz" : OpCodes.JZ, "jnz" : OpCodes.JNZ, "mlu" : OpCodes.MLU,
               "modify-case" : OpCodes.MODIFY_CASE, "push" : OpCodes.PUSH,
               "pushbl" : OpCodes.PUSHBL, "pushsb" : OpCodes.PUSHSB,
               "lu" : OpCodes.LU, "lu-count" : OpCodes.LU_COUNT,
               "not" : OpCodes.NOT, "out" : OpCodes.OUT, "ret" : OpCodes.RET,
               "storecl" : OpCodes.STORECL, "storesl" : OpCodes.STORESL,
               "storetl" : OpCodes.STORETL, "storev" : OpCodes.STOREV,
               "case-of" : OpCodes.CASE_OF
              }

    #For debugging purposes dict with opCode as key and string as value.
    reversedOpCodes = dict([(v, k) for k, v in opCodes.items()])

    def __init__(self, vm, t1xFile):
        #Access to the data structures of the vm is needed.
        self.vm = vm
        self.data = t1xFile

        #We convert the macro's name to a numerical address, used for indexing.
        self.macroNumber = {}
        self.macroName = None
        self.nextMacroNumber = -1

        #We convert each label to an internal numerical address, used by the vm.
        #Labels have different scopes: code, rules, macros...
        self.scopes = []
        self.currentScope = None

        #Define some constants to handle instructions by groups.
        self.instrWithLabel = [self.opCodes["addtrie"], self.opCodes["call"],
                               self.opCodes["jmp"], self.opCodes["jz"],
                               self.opCodes["jnz"]]

        #The current line number is used in the error messages.
        self.currentLineNumber = -1

    def raiseError(self, msg):
        """Raise an error to handle it in the main process."""

        raise LoaderError("line {}, {}".format(self.currentLineNumber, msg))

    def createNewScope(self):
        """Create a new scope and set it as the current one."""

        self.scopes.append(Scope())
        self.currentScope = self.scopes[-1]

    def deleteCurrentScope(self):
        """Delete the current scope."""

        self.scopes.pop()
        if len(self.scopes) > 0: self.currentScope = self.scopes[-1]
        else: self.currentScope = None

    def getRuleNumber(self, ruleLabel):
        """Get the number assigned to a rule by the compiler."""

        startIndex = ruleLabel.find('_') + 1
        endIndex = ruleLabel.rfind('_')
        return int(ruleLabel[startIndex:endIndex])

    def getNextMacroNumber(self):
        """Get a new unique address for a macro."""

        self.nextMacroNumber += 1
        return self.nextMacroNumber

    def getMacroName(self, name):
        """Get the name of a macro inside a label."""

        startIndex = name.find('_') + 1
        endIndex = name.rfind('_')
        return name[startIndex:endIndex]

    def getInternalRepresentation(self, line, section):
        """Get the vm representation of an assembly instruction."""

        #First, we get the opCode of the instruction.
        instr = line.strip().split(None, 1)
        try:
            opCode = self.opCodes[instr[0]]
        except KeyError:
            if ':' in line:
                label = instr[0].replace(':', '')
                self.currentScope.createNewLabelAddress(label)
                return
            else: self.raiseError("Unrecognized instruction: " + line)

        #Then, we handle the operand.
        if len(instr) == 1: return [opCode]
        else:
            if opCode in self.instrWithLabel:
                if opCode == self.opCodes['addtrie']:
                    instr[1] = self.getRuleNumber(instr[1])
                elif opCode == self.opCodes['call']:
                    instr[1] = self.macroNumber[instr[1]]
                else:
                    label = instr[1].replace(':\n', '')
                    instr[1] = \
                        self.currentScope.getReferenceToLabel(label, section)
            return [opCode, instr[1]]

    def addCodeToSection(self, code, section):
        """Add some code fragments to the section passed as argument."""

        if code:
            section.append(code)
            self.currentScope.nextAddress += 1

    def load(self):
        """
        Load an assembly file and transform the instructions to the vm
        representation, substituting macro or rules names for addresses.
        """

        #The default section is the vm.code with a default scope.
        self.createNewScope()
        currentSection = self.vm.code

        for number, line in enumerate(self.data.readlines()):
            self.currentLineNumber = number
            #Ignore comments.
            if line[0] == '#': continue

            #Handle the patterns and addtries.
            elif line.startswith('patterns'):
                #At the start, create a list which for the pattern's code.
                if line.endswith('start:\n'):
                    currentSection = []
                #At the end, add all the pattern's code to the preload section.
                elif line.endswith('end:\n'):
                    for code in currentSection:
                        self.vm.preprocessCode.append(code)
                    currentSection = self.vm.code

            #Handle the contents of each rule.
            elif line.startswith('action'):
                #At the start, create a list which will contain the rule's code.
                if line.endswith('start:\n'):
                    ruleNumber = self.getRuleNumber(line)
                    currentSection = []
                    self.createNewScope()
                #At the end, create an entry on the rules section with the code.
                elif line.endswith('end:\n'):
                    self.currentScope.backPatchLabels(currentSection)
                    self.vm.rulesCode.insert(ruleNumber, currentSection)
                    currentSection = self.vm.code
                    self.deleteCurrentScope()

            #Handle the contents of each macro.
            elif line.startswith('macro'):
                #At the start create a list which will contain the macro's code.
                if line.endswith('start:\n'):
                    macroName = self.getMacroName(line)
                    address = self.getNextMacroNumber()
                    self.macroNumber[macroName] = address
                    currentSection = []
                    self.createNewScope()
                #At the end create an entry on the macros section with the code.
                elif 'end:' in line:
                    self.addCodeToSection([self.opCodes['ret']], currentSection)
                    self.currentScope.backPatchLabels(currentSection)
                    self.vm.macrosCode.insert(address, currentSection)
                    currentSection = self.vm.code
                    self.deleteCurrentScope()

            #Handle all the simple instructions.
            else:
                internalRep = self.getInternalRepresentation(line, currentSection)
                self.addCodeToSection(internalRep, currentSection)

        #Finally we backpatch the root scope if needed and delete it.
        self.currentScope.backPatchLabels(currentSection)
        self.deleteCurrentScope()

        #Set the final address of the code loaded.
        self.vm.finalAddress = len(self.vm.code)

    def printSection(self, section, headerText, enum=False):
        """Print a code section for information or debugging purposes."""

        symbol = '='
        header = symbol * 20 + " {:=<39}"
        footer = symbol * 60 + '\n'

        if not enum:
            print(header.format(headerText + " section "))
            for number, code in enumerate(section):
                self.printInstruction(code, number)
        else:
            print(header.format(headerText + " code section "))
            for number, code in enumerate(section):
                print("\n{} {}:".format(headerText[:-1], number))
                for v, c in enumerate(code):
                    self.printInstruction(c, v)

        print(footer)

    def printInstruction(self, instr, PC=None):
        """Print a instruction converted to assembly."""

        opCodes = self.reversedOpCodes
        opCode = opCodes[int(instr[0])]

        if len(instr) > 1:
            if opCode == "call": operand = self.getMacroNameFromNumber(instr[1])
            else: operand = instr[1]

            if PC is None: print(opCode, operand)
            else: print("{}\t{} {}".format(PC, opCode, operand))
        else:
            if PC is None: print(opCode)
            else: print("{}\t{}".format(PC, opCode))

    def getMacroNameFromNumber(self, number):
        """Get the name of a macro from its number, useful for debugging."""

        if self.macroName is None:
            self.macroName = dict([(v, k) for k, v in self.macroNumber.items()])

        return self.macroName[number]
