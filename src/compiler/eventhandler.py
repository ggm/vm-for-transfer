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
from compilererror import CompilerError

class EventHandler():
    """Contains all the handlers of the XML events generated by the parser."""
    
    def __init__(self, compiler):
        self.logger = logging.getLogger('compiler')

        #Store the transfer stage of the file read as input.
        self.transferStage = ""

        #We need references to the compiler's data structures.
        self.defCats = compiler.defCats
        self.currentDefCat = None           #Keep the current cat to avoid extra calls to the stack.
        self.defAttrs = compiler.defAttrs
        self.currentDefAttrs = None         #Keep the current attr to avoid extra calls to the stack.
        self.defVars = compiler.defVars
        self.defLists = compiler.defLists
        self.currentDefList = None          #Keep the current list to avoid extra calls to the stack.
        
        #Assign some of the compiler's components needed
        self.callStack = compiler.callStack
        self.codeGen = compiler.codeGenerator
        self.symbolTable = compiler.symbolTable

    def raiseError(self, msg, event):
        raise CompilerError("line {}, {}".format(event.lineNumber, msg))

    def checkAttributeExists(self, event, attr):
        if attr not in event.attrs:
            self.raiseError("{} needs attribute {}.".format(event.name, attr), event)

    def handle_default_start(self, event):
        self.logger.debug("Ignoring call to unimplemented start handler for '{}' with attributes: {}".format(event.name, event.attrs))

    def handle_default_end(self, event):
        self.logger.debug("Ignoring call to unimplemented end handler for '{}'".format(event.name))

    def handle_transfer_start(self, event):
        self.transferStage = "chunk"
        self.codeGen.genTransferStart(event)
        
    def handle_interchunk_start(self, event):
        self.transferStage = "interchunk"
        self.codeGen.genInterchunkStart(event)

    def handle_postchunk_start(self, event):
        self.transferStage = "postchunk"
        self.codeGen.genPostchunkStart(event)

    def handle_def_cat_start(self, event):
        self.printDebugMessage("handle_def_cat_start", event)
        self.checkAttributeExists(event, 'n')
        defCatId = event.attrs['n']
        self.defCats[defCatId] = []
        self.currentDefCat = self.defCats[defCatId]
        
    def handle_def_cat_end(self, event):
        self.printDebugMessage("handle_def_cat_end")
        self.currentDefCat = None
        
    def handle_cat_item_start(self, event):
        self.printDebugMessage("handle_cat_item_start", event)
        catItem = ''
        if self.transferStage == "postchunk":
            catItem = event.attrs['name']
        else:
            if 'lemma' in event.attrs:                  #lemma attribute is optional.
                lemma = event.attrs['lemma']
                catItem = lemma
            
            if 'tags' in event.attrs:
                for tag in event.attrs['tags'].split('.'):
                    tag = "<{}>".format(tag)
                    catItem += tag
        
        self.currentDefCat.append(catItem)
    
    def handle_def_attr_start(self, event):
        self.printDebugMessage("handle_def_attr_start", event)
        self.checkAttributeExists(event, 'n')
        defAttrId = event.attrs['n']
        self.defAttrs[defAttrId] = []
        self.currentDefAttr = self.defAttrs[defAttrId]
        
    def handle_def_attr_end(self, event):
        self.printDebugMessage("handle_def_attr_end")
        self.currentDefAttr = None
        
    def handle_attr_item_start(self, event):
        self.printDebugMessage("handle_attr_item_start", event)
        attrItem = ''        
        for tag in event.attrs['tags'].split('.'):
            tag = "<{}>".format(tag)
            attrItem += tag
        
        self.currentDefAttr.append(attrItem)
        
    def handle_def_var_start(self, event):
        self.printDebugMessage("handle_def_var_start", event)
        self.checkAttributeExists(event, 'n')
        varName = event.attrs['n']
        defaultValue = ""
        if 'v' in event.attrs:
            defaultValue = event.attrs['v']
            if ';' in defaultValue:
                defaultValue = self.unEscape(defaultValue)
            self.codeGen.genDefVarStart(event, defaultValue)
        self.defVars[varName] = defaultValue
    
    def handle_def_list_start(self, event):
        self.printDebugMessage("handle_def_list_start", event)
        self.checkAttributeExists(event, 'n')
        defListId = event.attrs['n']
        self.defLists[defListId] = []
        self.currentDefList = self.defLists[defListId]
        
    def handle_def_list_end(self, event):
        self.printDebugMessage("handle_def_list_end")
        self.currentDefList = None
        
    def handle_list_item_start(self, event):
        self.printDebugMessage("handle_list_item_start", event)
        self.checkAttributeExists(event, 'v')
        listItem = event.attrs['v']
        self.currentDefList.append(listItem)

    def handle_section_def_macros_start(self, event):
        self.codeGen.genSectionDefMacrosStart(event)

    def handle_def_macro_start(self, event):
        self.checkAttributeExists(event, 'n')
        name = event.attrs['n']
        self.checkAttributeExists(event, 'npar')
        npar = event.attrs['npar']
        self.symbolTable.addMacro(name, npar)
        self.codeGen.genDefMacroStart(event)

    def handle_def_macro_end(self, event):
        self.codeGen.genDefMacroEnd(event)
        
    def handle_section_rules_start(self, event):
        self.printDebugMessage("handle_section_rules_start", event)
        self.codeGen.genSectionRulesStart(event)

    def handle_section_rules_end(self, event):
        self.printDebugMessage("handle_section_rules_end", event)
        self.codeGen.genSectionRulesEnd(event)

    def handle_rule_start(self, event):
        self.codeGen.genRuleStart(event)

    def handle_pattern_end(self, event):
        self.codeGen.genPatternEnd(event)

    def handle_pattern_item_end(self, event):
        self.checkAttributeExists(event, 'n')
        catName = event.attrs['n']
        if catName not in self.defCats:
            self.raiseError("cat '{}' doesn't exist.".format(catName), event)
        cats = self.defCats[catName]
        self.codeGen.genPatternItemEnd(event, cats)

    def handle_action_start(self, event):
        event.variables['label'] = event.parent.variables['label']
        self.codeGen.genActionStart(event)

    def handle_action_end(self, event):
        self.codeGen.genActionEnd(event)

    def handle_call_macro_start(self, event):
        self.codeGen.genCallMacroStart(event)
        self.checkAttributeExists(event, 'n')

    def handle_call_macro_end(self, event):
        macroName = event.attrs['n']
        #In one pass we can only check for the macros already parsed.
        if macroName in self.symbolTable.symbols:
            numParams = event.numChildren
            numParamsSymb = self.symbolTable.symbols[macroName].numParams
            if int(numParams) != int(numParamsSymb):
                self.raiseError("Macro '{}' needs {} parameters, passed {}."
                                .format(macroName, numParamsSymb, numParams), event)
        self.codeGen.genCallMacroEnd(event)

    def handle_with_param_end(self, event):
        self.codeGen.genWithParamEnd(event)

    def handle_choose_start(self, event):
        self.codeGen.genChooseStart(event)

    def handle_choose_end(self, event):
        self.codeGen.genChooseEnd(event)

    def handle_when_start(self, event):
        self.codeGen.genWhenStart(event)

    def handle_when_end(self, event):
        self.codeGen.genWhenEnd(event)

    def handle_otherwise_start(self, event):
        self.codeGen.genOtherwiseStart(event)

    def handle_test_end(self, event):
        self.codeGen.genTestEnd(event)

    def handle_b_start(self, event):
        self.codeGen.genBStart(event)

    def handle_lit_start(self, event):
        self.codeGen.genLitStart(event)

    def handle_lit_tag_start(self, event):
        self.codeGen.genLitTagStart(event)

    def handle_tags_end(self, event):
        self.codeGen.genTagsEnd(event)

    def handle_lu_end(self, event):
        self.codeGen.genLuEnd(event)

    def handle_mlu_end(self, event):
        self.codeGen.genMluEnd(event)

    def handle_lu_count_end(self, event):
        self.codeGen.genLuCountEnd(event)

    def handle_chunk_start(self, event):
        self.codeGen.genChunkStart(event)

    def handle_chunk_end(self, event):
        self.codeGen.genChunkEnd(event)

    def handle_equal_end(self, event):
        self.codeGen.genEqualEnd(event)

    def handle_and_end(self, event):
        self.codeGen.genAndEnd(event)

    def handle_or_end(self, event):
        self.codeGen.genOrEnd(event)

    def handle_not_end(self, event):
        self.codeGen.genNotEnd(event)

    def handle_out_end(self, event):
        self.codeGen.genOutEnd(event)

    def handle_var_start(self, event):
        self.checkAttributeExists(event, 'n')
        varName = event.attrs['n']
        if varName not in self.defVars:
            self.raiseError("var '{}' doesn't exist.".format(varName), event)
        self.codeGen.genVarStart(event)

    def handle_in_end(self, event):
        self.codeGen.genInEnd(event)

    def handle_clip_end(self, event):
        #If there is a link-to attribute, we ignore the other ones.
        partAttrs = []
        if 'link-to' in event.attrs:
            linkTo = True
        else:
            linkTo = False
            part = event.attrs['part']
            if part not in self.defAttrs:
                if part in "lem lemh lemq whole tags": partAttrs.append(part)
                else: self.raiseError("attr '{}' doesn't exist.".format(part), event)
            else: partAttrs = self.defAttrs[part]

        isContainer = False
        if event.parent.name in ('let', 'modify-case'):
            if event.parent.numChildren == 1: #If it's the first child, it's on the left
                isContainer = True    #therefore it's a container.
        self.codeGen.genClipEnd(event, partAttrs, isContainer, linkTo)

    def handle_list_start(self, event):
        self.checkAttributeExists(event, 'n')
        listName = event.attrs['n']
        if listName not in self.defLists:
            self.raiseError("list '{}' doesn't exist.".format(listName), event)
        list = self.defLists[listName]
        self.codeGen.genListStart(event, list)

    def handle_let_end(self, event):
        container = event.children[0]
        self.codeGen.genLetEnd(event, container)

    def handle_concat_end(self, event):
        self.codeGen.genConcatEnd(event)

    def handle_append_start(self, event):
        self.codeGen.genAppendStart(event)

    def handle_append_end(self, event):
        self.codeGen.genAppendEnd(event)

    def handle_get_case_from_start(self, event):
        self.codeGen.genGetCaseFromStart(event)

    def handle_get_case_from_end(self, event):
        self.codeGen.genGetCaseFromEnd(event)

    def handle_case_of_start(self, event):
        part = event.attrs['part']
        partAttrs = []
        if part in "lem lemh lemq whole": partAttrs.append(part)
        else: partAttrs = self.defAttrs[part]

        self.codeGen.genCaseOfStart(event, partAttrs)

    def handle_modify_case_end(self, event):
        container = event.children[0]
        self.codeGen.genModifyCaseEnd(event, container)

    def handle_begins_with_end(self, event):
        self.codeGen.genBeginsWithEnd(event)

    def handle_begins_with_list_end(self, event):
        self.codeGen.genBeginsWithEnd(event)

    def handle_ends_with_end(self, event):
        self.codeGen.genEndsWithEnd(event)

    def handle_ends_with_list_end(self, event):
        self.codeGen.genEndsWithEnd(event)

    def handle_contains_substring_end(self, event):
        self.codeGen.genContainsSubstringEnd(event)

    def printDebugMessage(self, methodName, event=None):
        """Prints the call of a method, given the method name and an optional event."""
        if (not event):
            self.logger.debug("{}()".format(methodName))
        else:
            self.logger.debug("{}: (<{} {}>)".format(methodName, event.name, event.attrs))
            
    def unEscape(self, v):
        """Unescape values of the xml file (<, >, &) and leaves them on tag form."""
        v = v.replace("&lt;", "<")
        v = v.replace("&gt;", ">")
        v = v.replace("&amp;", "")
        return v
