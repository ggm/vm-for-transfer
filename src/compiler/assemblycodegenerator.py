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

    AND_OP = "and"          #and num -> and of the last num elements on the stack.
    OR_OP = "or"            #or num -> or of the last num elements on the stack.
    CLIPSL_OP = "clipsl"    #clipsl -> puts a substring of the source language on the stack.
    CLIPTL_OP = "cliptl"    #cliptl -> puts a substring of the target language on the stack.
    CMP_OP = "cmp"          #cmp -> compares the last two items on the stack.
                            #       and leaves 0 (not equal) or 1 (equal).
    CMPI_OP = "cmpi"        #cmpi -> same as cmp but ignoring the case.
    GET_CASE_FROM_OP = "get-case-from" #get the case from contens in pos.
    IN_OP = "in"            #in -> search a value in a list.
    INIG_OP = "inig"        #inig -> search a value in a list, ignoring case.
    JMP_OP = "jmp"          #jmp label -> jumps to the label, unconditionally.
    JZ_OP = "jz"            #jz label -> jumps to label if stack.top == 0.
    PUSH_OP = "push"        #push value -> pushes a value to the stack.
    PUSHBL_OP = "pushbl"    #pushbl -> pushes a blank to the stack.
    PUSHSB_OP = "pushsb"    #pushsb pos -> pushes a superblank at pos.
    NOT_OP = "not"          #not -> negates the stack top (0 -> 1, 1 -> 0).
    OUT_OP = "out"          #out num -> outputs a number of elements on the stack.
    STORESL_OP = "storesl"  #storesl -> stores the top in the source language.
    STORETL_OP = "storetl"  #storetl -> stores the top in the target language.
    STOREV_OP = "storev"    #storev -> stack(value, variable, ...) stores value in variable.

    def __init__(self):
        self.logger = logging.getLogger('compiler')
        self.debug = False

        #The code we are going to generate.
        self.code = []

        #Used to get the next address of an instruction if needed.
        self.nextAddress = 0

        #Used to generate new labels by element type.
        self.nextLabel = {'when' : 0, 'choose' : 0}

    def addCode(self, code):
        self.code.append(code)
        self.nextAddress += 1

    def getNextLabel(self, elem):
        nextLabel = self.nextLabel[elem]
        self.nextLabel[elem] += 1
        return nextLabel

    def getWritableCode(self):
        return '\n'.join(self.code).encode('utf-8')

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

    def genChooseStart(self, event):
        event.variables['label'] = self.getNextLabel("choose")

    def genChooseEnd(self, event):
        numLabel = event.variables['label']
        self.addCode("choose_{}_end:".format(numLabel))

    def genWhenStart(self, event):
        event.variables['label'] = self.getNextLabel("when")

    def genWhenEnd(self, event, parent):
        #Add a jump to the end of the choose element, if the when is successful.
        numLabel = parent.variables['label']
        self.addCode(self.JMP_OP  + self.INSTR_SEP + "choose_{}_end".format(numLabel))

        #Add the label of the when end.
        numLabel = event.variables['label']
        self.addCode("when_{}_end:".format(numLabel))

    def genOtherwiseStart(self, event):
        self.genDebugCode(event)

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

    def genLitTagStart(self, event):
        self.genDebugCode(event)

        #Convert <det.ind> to <det><ind> format.
        litTag = "\"<{}>\"".format(event.attrs['v'])
        litTag = litTag.replace(".", "><")
        self.addCode(self.PUSH_OP + self.INSTR_SEP + litTag)

    def genEqualEnd(self, event):
        if 'caseless' not in event.attrs: self.addCode(self.CMP_OP)
        else:
            caseless = event.attrs['caseless']
            if caseless == "no": self.addCode(self.CMP_OP)
            elif caseless == "yes": self.addCode(self.CMPI_OP)

    def genAndEnd(self, event):
        self.addCode(self.AND_OP + self.INSTR_SEP + str(event.numChilds))

    def genOrEnd(self, event):
        self.addCode(self.OR_OP + self.INSTR_SEP + str(event.numChilds))

    def genNotEnd(self, event):
        self.addCode(self.NOT_OP)

    def genOutEnd(self, event):
        self.addCode(self.OUT_OP + self.INSTR_SEP + str(event.numChilds))

    def genVarStart(self, event):
        self.genDebugCode(event)
        self.addCode(self.PUSH_OP + self.INSTR_SEP + event.attrs['n'])

    def genInEnd(self, event):
        if 'caseless' not in event.attrs: self.addCode(self.IN_OP)
        else:
            caseless = event.attrs['caseless']
            if caseless == "no": self.addCode(self.IN_OP)
            elif caseless == "yes": self.addCode(self.INIG_OP)

    def genClipStart(self, event, partAttrs):
        self.genDebugCode(event)

        #Push the position to the stack.
        pos = event.attrs['pos']
        self.addCode(self.PUSH_OP + self.INSTR_SEP + str(pos))

        #Push the contents of the part attribute.
        if len(partAttrs) == 1: partAttrStr = "\"{}\"".format(partAttrs[0])
        else: partAttrStr = "\"" + "|".join(partAttrs) + "\""
        self.addCode(self.PUSH_OP + self.INSTR_SEP + partAttrStr)

        #Choose the appropriate instr depending on the side of the clip op.
        if event.attrs['side'] == 'sl': self.addCode(self.CLIPSL_OP)
        elif event.attrs['side'] == 'tl': self.addCode(self.CLIPTL_OP)

    def genListStart(self, event, list):
        self.genDebugCode(event)

        #Push the contents of the list to the stack.
        if len(list) == 1: list = "\"{}\"".format(list[0])
        else: list = "\"" + "|".join(list) + "\""
        self.addCode(self.PUSH_OP + self.INSTR_SEP + list)

    def genLetEnd(self, event, container):
        instr = None

        #Choose the appropriate instr depending on the container.
        if 'var' in container.name: instr = self.STOREV_OP
        elif 'clip' in container.name:
            if container.attrs['side'] == 'sl': instr = self.STORESL_OP
            elif container.attrs['side'] == 'tl': instr = self.STORETL_OP

        self.addCode(instr)

    def genGetCaseFromStart(self, event):
        self.genDebugCode(event)

    def genGetCaseFromEnd(self, event):
        pos = event.attrs['pos']
        self.addCode(self.PUSH_OP + self.INSTR_SEP + str(pos))
        self.addCode(self.GET_CASE_FROM_OP)

    def genDebugCode(self, event):
        """Generate debug messages if debug is on."""
        if not self.debug:
            return

        attrs = ""
        for k, v in event.attrs.items():
            attrs += " {}=\"{}\"".format(k, v)

        debugInfo = "#<{}{}>".format(event.name, attrs)
        self.code.append(debugInfo)
