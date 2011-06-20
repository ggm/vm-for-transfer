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
    INSTR_SEP = " "         #instruction and arguments separator (' ', '\t').

    ADDTRIE_OP = "addtrie"  #addtrie addr -> add a set of patterns to the trie.
    AND_OP = "and"          #and num -> and of the last num elements on the stack.
    APPEND_OP = "append"    #append num -> append the last num elements on the stack to a var/clip.
    BEGINS_WITH_OP = "begins-with" #begins-with(-ig) -> tests if the first op contains the
    BEGINS_WITH_IG_OP = "begins-with-ig" #second one at the beginning (ig -> ignore case).
    OR_OP = "or"            #or num -> or of the last num elements on the stack.
    CALL_OP = "call"        # call name -> call a macro with the arguments on the stack.
    CMP_SUBSTR_OP = "cmp-substr" #cmp(i)-substr -> tests if the first op contains the
    CMPI_SUBSTR_OP = "cmpi-substr" #contains a substring of the second one (i -> ignore case).
    CLIP_OP = "clip"        #clip -> In t2x/t3x there is only a language, we don't need a side.
    CLIPSL_OP = "clipsl"    #clipsl -> puts a substring of the source language on the stack.
    CLIPTL_OP = "cliptl"    #cliptl -> puts a substring of the target language on the stack.
    CMP_OP = "cmp"          #cmp -> compares the last two items on the stack.
                            #       and leaves 0 (not equal) or 1 (equal).
    CMPI_OP = "cmpi"        #cmpi -> same as cmp but ignoring the case.
    CONCAT_OP = "concat"    # concat num -> concat last num items on the stack.
    CHUNK_OP = "chunk"      #chunk num -> creates a chunk with num operands on the stack.
    ENDS_WITH_OP = "ends-with" #ends-with(-ig) -> tests if the first op contains the
    ENDS_WITH_IG_OP = "ends-with-ig" #second one at the beginning (ig -> ignore case).
    GET_CASE_FROM_OP = "get-case-from" #get the case from contents in pos.
    IN_OP = "in"            #in -> search a value in a list.
    INIG_OP = "inig"        #inig -> search a value in a list, ignoring case.
    JMP_OP = "jmp"          #jmp label -> jumps to the label, unconditionally.
    JZ_OP = "jz"            #jz label -> jumps to label if stack.top == 0.
    MLU_OP = "mlu"          #mlu num -> creates a multiword with num elements.
    MODIFY_CASE_OP = "modify-case" #modify-case -> copy the case of one element to another.
    PUSH_OP = "push"        #push value -> pushes a value to the stack.
    PUSHBL_OP = "pushbl"    #pushbl -> pushes a blank to the stack.
    PUSHSB_OP = "pushsb"    #pushsb pos -> pushes a superblank at pos.
    LU_OP = "lu"            #lu num -> creates a lexical unit(^...$).
    LU_COUNT_OP = "lu-count"#lu-count -> counts number of lexical units in the rule (chunk).
    NOT_OP = "not"          #not -> negates the stack top (0 -> 1, 1 -> 0).
    OUT_OP = "out"          #out num -> outputs a number of elements on the stack.
    RET_OP = "ret"          #ret -> returns from a macro.
    STORECL_OP = "storecl"  #storecl -> stores the top in the clip (interchunk, postchunk).
    STORESL_OP = "storesl"  #storesl -> stores the top in the source language.
    STORETL_OP = "storetl"  #storetl -> stores the top in the target language.
    STOREV_OP = "storev"    #storev -> stack(value, variable, ...) stores value in variable.

    def __init__(self):
        self.logger = logging.getLogger('compiler')
        self.debug = False

        #The code we are going to generate, separating the contents of the rules,
        #the actions, from the pattern of each rule. Every pattern goes to the
        #top of the section-rules section, and later on all the action code.
        self.code = []
        self.patternsCode = []
        self.patternsSection = 0

        #Used to get the next address of an instruction if needed.
        self.nextAddress = 0

        #Used to generate new labels by element type.
        self.nextLabel = {'when' : 0, 'choose' : 0, 'rule' : 0}

    def addCode(self, code):
        self.code.append(code)
        self.nextAddress += 1

    def addPatternsCode(self, code):
        self.patternsCode.append(code)
        self.nextAddress += 1

    def getNextLabel(self, elem):
        nextLabel = self.nextLabel[elem]
        self.nextLabel[elem] += 1
        return nextLabel

    def getWritableCode(self):
        #Insert the patterns section code in its place.
        code = self.code[:self.patternsSection] + self.patternsCode + self.code[self.patternsSection:]
        writableCode = '\n'.join(code)
        writableCode += '\n'
        writableCode = writableCode.encode('utf-8')
        return writableCode

    def genStoreInstr(self, container):
        #Choose the appropriate instr depending on the container.
        if 'var' in container.name: return self.STOREV_OP
        elif 'clip' in container.name:
            if 'side' not in container.attrs: return self.STORECL_OP
            elif container.attrs['side'] == 'sl': return self.STORESL_OP
            elif container.attrs['side'] == 'tl': return self.STORETL_OP

    def getIgnoreCaseInstr(self, event, instrNotIgnoreCase, instrIgnoreCase):
        if 'caseless' not in event.attrs: return instrNotIgnoreCase
        else:
            caseless = event.attrs['caseless']
            if caseless == "no": return instrNotIgnoreCase
            elif caseless == "yes": return instrIgnoreCase

    def genHeader(self, event):
        #Add the type of file so the vm can read it accordingly.
        self.addCode("#<assembly>")
        #Add the rest of the header as the first element of the xml.
        attrs = ""
        for k, v in event.attrs.items():
            attrs += " {}=\"{}\"".format(k, v)

        header = "#<{}{}>".format(event.name, attrs)
        self.addCode(header)

    def genTransferStart(self, event):
        self.genHeader(event)

    def genInterchunkStart(self, event):
        self.genHeader(event)

    def genPostchunkStart(self, event):
        self.genHeader(event)

    def genDefVarStart(self, event, defaultValue):
        self.genDebugCode(event)
        #Push the default value and store it in var.
        self.addCode(self.PUSH_OP + self.INSTR_SEP + event.attrs['n'])
        self.addCode(self.PUSH_OP + self.INSTR_SEP
                     + "\"{}\"".format(str(defaultValue)))
        self.addCode(self.STOREV_OP)

    def genSectionDefMacrosStart(self, event):
        #Jump to the start of the rules, ignoring the macros until called.
        self.addCode(self.JMP_OP + self.INSTR_SEP + "section_rules_start")

    def genDefMacroStart(self, event):
        self.genDebugCode(event)
        self.addCode("macro_{}_start:".format(event.attrs['n']))

    def genDefMacroEnd(self, event):
        macroEndLabel = "macro_{}_end:".format(event.attrs['n'])
        self.addCode(macroEndLabel + self.INSTR_SEP + self.RET_OP)

    def genSectionRulesStart(self, event):
        self.genDebugCode(event)
        self.addCode("section_rules_start:")
        self.patternsSection = self.nextAddress

    def genSectionRulesEnd(self, event):
        self.addCode("section_rules_end:")

    def genRuleStart(self, event):
        event.variables['label'] = self.getNextLabel("rule")

    def genPatternEnd(self, event):
        #Push the number of patterns to add to the trie.
        self.addPatternsCode(self.PUSH_OP + self.INSTR_SEP + str(event.numChildren))
        #Push the trie instruction with the destination address as operand.
        numLabel = event.parent.variables['label']
        self.addPatternsCode(self.ADDTRIE_OP + self.INSTR_SEP + "action_{}_start".format(numLabel))

    def genPatternItemEnd(self, event, cats):
        #Push the contents of the category.
        if len(cats) == 1: catsStr = "\"{}\"".format(cats[0])
        else: catsStr = "\"" + "|".join(cats) + "\""
        self.addPatternsCode(self.PUSH_OP + self.INSTR_SEP + catsStr)

    def genActionStart(self, event):
        numLabel = event.variables['label']
        self.addCode("action_{}_start:".format(numLabel))

    def genActionEnd(self, event):
        numLabel = event.variables['label']
        self.addCode("action_{}_end:".format(numLabel))

    def genCallMacroStart(self, event):
        self.genDebugCode(event)

    def genCallMacroEnd(self, event):
        self.addCode(self.PUSH_OP + self.INSTR_SEP + str(event.numChildren))
        self.addCode(self.CALL_OP + self.INSTR_SEP + event.attrs['n'])

    def genWithParamEnd(self, event):
        self.addCode(self.PUSH_OP + self.INSTR_SEP + str(event.attrs['pos']))

    def genChooseStart(self, event):
        event.variables['label'] = self.getNextLabel("choose")

    def genChooseEnd(self, event):
        numLabel = event.variables['label']
        self.addCode("choose_{}_end:".format(numLabel))

    def genWhenStart(self, event):
        event.variables['label'] = self.getNextLabel("when")

    def genWhenEnd(self, event):
        #Add a jump to the end of the choose element, if the when is successful.
        numLabel = event.parent.variables['label']
        self.addCode(self.JMP_OP  + self.INSTR_SEP + "choose_{}_end".format(numLabel))

        #Add the label of the when end.
        numLabel = event.variables['label']
        self.addCode("when_{}_end:".format(numLabel))

    def genOtherwiseStart(self, event):
        self.genDebugCode(event)

    def genTestEnd(self, event):
        numLabel = event.parent.variables['label']
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

    def genTagsEnd(self, event):
        if event.numChildren > 1:
            self.addCode(self.APPEND_OP + self.INSTR_SEP + str(event.numChildren))

    def genLuEnd(self, event):
        self.addCode(self.LU_OP + self.INSTR_SEP + str(event.numChildren))

    def genMluEnd(self, event):
        self.addCode(self.MLU_OP + self.INSTR_SEP + str(event.numChildren))

    def genLuCountEnd(self, event):
        self.addCode(self.LU_COUNT_OP)

    def genChunkStart(self, event):
        self.genDebugCode(event)
        chunkName = None    #Name is optional.
        
        #If there is a fromname we push the var name. 
        if 'fromname' in event.attrs: chunkName = event.attrs['fromname']
        elif 'name' in event.attrs: chunkName = "\"{}\"".format(event.attrs['name'])
        if chunkName: 
            self.addCode(self.PUSH_OP + self.INSTR_SEP + chunkName)
            event.variables['name'] = True

    def genChunkEnd(self, event):
        numOps = event.numChildren
        if 'name' in event.variables: numOps += 1
        self.addCode(self.CHUNK_OP + self.INSTR_SEP + str(numOps))

    def genEqualEnd(self, event):
        self.addCode(self.getIgnoreCaseInstr(event, self.CMP_OP, self.CMPI_OP))

    def genAndEnd(self, event):
        self.addCode(self.AND_OP + self.INSTR_SEP + str(event.numChildren))

    def genOrEnd(self, event):
        self.addCode(self.OR_OP + self.INSTR_SEP + str(event.numChildren))

    def genNotEnd(self, event):
        self.addCode(self.NOT_OP)

    def genOutEnd(self, event):
        self.addCode(self.OUT_OP + self.INSTR_SEP + str(event.numChildren))

    def genVarStart(self, event):
        self.genDebugCode(event)
        self.addCode(self.PUSH_OP + self.INSTR_SEP + event.attrs['n'])

    def genInEnd(self, event):
        self.addCode(self.getIgnoreCaseInstr(event, self.IN_OP, self.INIG_OP))

    def genClipCode(self, event, partAttrs, linkTo=False):
        #If there is a link-to attribute, we ignore the other ones.
        if linkTo:
            link_to = "\"<{}>\"".format(str(event.attrs['link-to']))
            self.addCode(self.PUSH_OP + self.INSTR_SEP + link_to)
            return

        #Push the position to the stack.
        pos = event.attrs['pos']
        self.addCode(self.PUSH_OP + self.INSTR_SEP + str(pos))

        #Push the contents of the part attribute.
        if len(partAttrs) == 1: partAttrStr = "\"{}\"".format(partAttrs[0])
        else: partAttrStr = "\"" + "|".join(partAttrs) + "\""
        self.addCode(self.PUSH_OP + self.INSTR_SEP + partAttrStr)

    def genClipInstr(self, event):
        #Choose the appropriate instr depending on the side of the clip op.
        if 'side' not in event.attrs: self.addCode(self.CLIP_OP)
        elif event.attrs['side'] == 'sl': self.addCode(self.CLIPSL_OP)
        elif event.attrs['side'] == 'tl': self.addCode(self.CLIPTL_OP)

    def genClipEnd(self, event, partAttrs, isContainer, linkTo):
        self.genDebugCode(event)

        self.genClipCode(event, partAttrs, linkTo)

        #If this clip doesn't work as a container (left-side), we need a CLIP(SL|TL).
        if not linkTo and not isContainer:
            self.genClipInstr(event)

    def genListStart(self, event, list):
        self.genDebugCode(event)

        #Push the contents of the list to the stack.
        if len(list) == 1: list = "\"{}\"".format(list[0])
        else: list = "\"" + "|".join(list) + "\""
        self.addCode(self.PUSH_OP + self.INSTR_SEP + list)

    def genLetEnd(self, event, container):
        self.addCode(self.genStoreInstr(container))

    def genConcatEnd(self, event):
        self.addCode(self.CONCAT_OP + self.INSTR_SEP + str(event.numChildren))

    def genAppendStart(self, event):
        self.genDebugCode(event)
        self.addCode(self.PUSH_OP + self.INSTR_SEP + event.attrs['n'])

    def genAppendEnd(self, event):
        self.addCode(self.APPEND_OP + self.INSTR_SEP + str(event.numChildren))

    def genGetCaseFromStart(self, event):
        self.genDebugCode(event)

    def genGetCaseFromEnd(self, event):
        pos = event.attrs['pos']
        self.addCode(self.PUSH_OP + self.INSTR_SEP + str(pos))
        self.addCode(self.GET_CASE_FROM_OP)

    def genCaseOfStart(self, event, partAttrs):
        self.genDebugCode(event)

        #Generate the code of the clip we are going to get the case from.
        self.genClipCode(event, partAttrs)
        #Add the clip instruction depending on the side attribute.
        self.genClipInstr(event)

        #Finally, use get-case-from to get the case of the clip on the stack.
        # "1" because the clip already extracted the pos.
        self.addCode(self.PUSH_OP + self.INSTR_SEP + "1")
        self.addCode(self.GET_CASE_FROM_OP)

    def genModifyCaseEnd(self, event, container):
        self.addCode(self.MODIFY_CASE_OP)
        self.addCode(self.genStoreInstr(container))

    def genBeginsWithEnd(self, event):
        self.addCode(self.getIgnoreCaseInstr(event, self.BEGINS_WITH_OP, self.BEGINS_WITH_IG_OP))

    def genEndsWithEnd(self, event):
        self.addCode(self.getIgnoreCaseInstr(event, self.ENDS_WITH_OP, self.ENDS_WITH_IG_OP))

    def genContainsSubstringEnd(self, event):
        self.addCode(self.getIgnoreCaseInstr(event, self.CMP_SUBSTR_OP, self.CMPI_SUBSTR_OP))

    def genDebugCode(self, event):
        """Generate debug messages if debug is on."""
        if not self.debug:
            return

        attrs = ""
        for k, v in event.attrs.items():
            attrs += " {}=\"{}\"".format(k, v)

        debugInfo = "#<{}{}>".format(event.name, attrs)
        self.addCode(debugInfo)
