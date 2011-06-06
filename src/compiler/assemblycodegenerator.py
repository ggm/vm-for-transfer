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
import logging

class AssemblyCodeGenerator:
    """This class generates code as a predefined pseudo-assembly."""
    
    #Define the instruction set as a set of constants to ease the creation
    #of other code generators.
    INSTR_SEP = " "         #instruction and argumentes separator (' ', '\t').

    CMP_OP = "cmp"          #cmp -> compares the last two items in the stack.
                            #       and leaves 0 (not equal) or 1 (equal).
    JMP_OP = "jmp"          #jmp label -> jumps to the label, unconditionally.
    JZ_OP = "jz"            #jz label -> jumps to label if stack.top == 0.
    PUSH_OP = "push"        #push value -> pushes a value to the stack.
    PUSHBL_OP = "pushbl"    #pushbl -> pushes a blank in the stack.
    PUSHSB_OP = "pushsb"    #pushsb pos -> pushes a superblank at pos.
    NOT_OP = "not"          #not -> negates the stack top (0 -> 1, 1 -> 0).
    OUT_OP = "out"          #out num -> outputs a number of elements in the stack.

    def __init__(self):
        self.logger = logging.getLogger('compiler')
        self.debug = False

        #The code we are going to generate.
        self.code = []

        #Used to get the next address of an instruction if needed.
        self.nextAddress = 0

        #Used to generate new labels by element type.
        self.nextLabel = {'when' : 0}

    def addCode(self, code):
        self.code.append(code)
        self.nextAddress += 1

    def getNextLabel(self, elem):
        nextLabel = self.nextLabel[elem]
        self.nextLabel[elem] += 1
        return nextLabel

    def genTransferStart(self, event):
        self.genDebugCode(event)
        #Jump to the start of the rules, ignoring the macros until called.
        self.addCode(self.JMP_OP + self.INSTR_SEP + "section_rules_start")

    def genDefMacroStart(self, event):
        self.genDebugCode(event)
        self.addCode("macro_{}_start:".format(event.attrs['n']))

    def genDefMacroEnd(self, event):
        self.addCode("macro_{}_end:".format(event.attrs['n']))

    def genSectionRulesStart(self, event):
        self.genDebugCode(event)
        self.addCode("section_rules_start:")

    def genSectionRulesEnd(self, event):
        self.addCode("section_rules_end:\n")

    def genWhenStart(self, event):
        event.variables['label'] = self.getNextLabel("when")

    def genWhenEnd(self, event):
        numLabel = event.variables['label']
        self.addCode("when_{}_end:".format(numLabel))

    def genTestEnd(self, event, parent):
        numLabel = parent.variables['label']
        self.addCode(self.JZ_OP + self.INSTR_SEP + "when_{}_end".format(numLabel))

    def genBStart(self, event):
        if 'pos' in event.attrs:
            self.addCode(self.PUSHSB_OP + self.INSTR_SEP + event.attrs['pos'])
        else:
            self.addCode(self.PUSHBL_OP)

    def genLitStart(self, event):
        self.genDebugCode(event)
        self.addCode(self.PUSH_OP + self.INSTR_SEP + "\"{}\"".format(event.attrs['v']))

    def genEqualEnd(self, event):
        self.addCode(self.CMP_OP)

    def genNotEnd(self, event):
        self.addCode(self.NOT_OP)

    def genOutEnd(self, event):
        self.addCode(self.OUT_OP + self.INSTR_SEP + str(event.numChilds))

    def genVarStart(self, event):
        self.genDebugCode(event)
        self.addCode(self.PUSH_OP + self.INSTR_SEP + event.attrs['n'])

    def genDebugCode(self, event):
        """Generate debug messages if debug is on."""
        if not self.debug:
            return

        attrs = ""
        for k, v in event.attrs.items():
            attrs += " {}=\"{}\"".format(k, v)

        debugInfo = "#<{}{}>".format(event.name, attrs)
        self.code.append(debugInfo)
