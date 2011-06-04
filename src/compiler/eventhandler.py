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

class EventHandler():
    """Contains all the handlers of the XML events generated by the parser."""
    
    def __init__(self, compiler, codeGenerator, symbolTable):
        self.logger = logging.getLogger('compiler')
        
        #We need references to the compiler's data structures.
        self.defCats = compiler.defCats
        self.currentDefCat = None           #Keep the current cat to avoid extra calls to the stack.
        self.defAttrs = compiler.defAttrs
        self.currentDefAttrs = None         #Keep the current attr to avoid extra calls to the stack.
        self.defVars = compiler.defVars
        self.defLists = compiler.defLists
        self.currentDefList = None          #Keep the current list to avoid extra calls to the stack.
        
        #Assign some of the compiler's components needed
        self.codeGen = codeGenerator
        self.symbolTable = symbolTable 
        
    def handle_transfer_start(self, event):
        self.codeGen.genTransferStart(event)
        
    def handle_transfer_end(self, event):
        self.codeGen.genTransferEnd(event)
    
    def handle_default_start(self, event):
        self.logger.debug("Ignoring call to unimplemented start handler for '{}' with attributes: {}".format(event.name, event.attrs))
        
    def handle_default_end(self, event):
        self.logger.debug("Ignoring call to unimplemented end handler for '{}'".format(event.name))
        
    def handle_def_cat_start(self, event):
        self.printDebugMessage("handle_def_cat_start", event)
        defCatId = event.attrs['n']
        self.defCats[defCatId] = []
        self.currentDefCat = self.defCats[defCatId]
        
    def handle_def_cat_end(self, event):
        self.printDebugMessage("handle_def_cat_end")
        self.currentDefCat = None
        
    def handle_cat_item_start(self, event):
        self.printDebugMessage("handle_cat_item_start", event)
        catItem = ''
        if 'lemma' in event.attrs:                  #lemma attribute is optional
            lemma = event.attrs['lemma']
            catItem = lemma
        
        for tag in event.attrs['tags'].split('.'):
            tag = "<{}>".format(tag)
            catItem += tag
        
        self.currentDefCat.append(catItem)
    
    def handle_def_attr_start(self, event):
        self.printDebugMessage("handle_def_attr_start", event)
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
        varName = event.attrs['n']
        defaultValue = ""
        if 'v' in event.attrs:
            defaultValue = event.attrs['v']
            if ';' in defaultValue:
                defaultValue = self.unEscape(defaultValue) 
        self.defVars[varName] = defaultValue
    
    def handle_def_list_start(self, event):
        self.printDebugMessage("handle_def_list_start", event)
        defListId = event.attrs['n']
        self.defLists[defListId] = []
        self.currentDefList = self.defLists[defListId]
        
    def handle_def_list_end(self, event):
        self.printDebugMessage("handle_def_list_end")
        self.currentDefList = None
        
    def handle_list_item_start(self, event):
        self.printDebugMessage("handle_list_item_start", event)
        listItem = event.attrs['v']        
        self.currentDefList.append(listItem)

    def handle_def_macro_start(self, event):
        name = event.attrs['n']
        npar = event.attrs['npar']
        self.symbolTable.addMacro(name, npar)
        self.codeGen.genDefMacroStart(event)

    def handle_def_macro_end(self, event):
        self.codeGen.genDefMacroEnd(event)
    
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
