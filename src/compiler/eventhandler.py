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
from assemblycodegenerator import AssemblyCodeGenerator

class EventHandler():
    """Contains all the handlers of the XML events generated by the parser."""
    
    def __init__(self, compiler):
        self.logger = logging.getLogger('compiler')
        
        #We need references to the compiler's data structures.
        self.defCats = compiler.defCats
        self.currentDefCat = None           #Keep the current cat to avoid extra calls to the stack.
        
        #In the future we could easily change it, e.g to a binary generator. 
        self.codeGen = AssemblyCodeGenerator()
    
    def handle_default_start(self, event):
        self.logger.debug("Ignoring call to unimplemented start handler for '{}' with attributes: {}".format(event.name, event.attrs))
        
    def handle_default_end(self, event):
        self.logger.debug("Ignoring call to unimplemented end handler for '{}'".format(event.name))
        
    def handle_def_cat_start(self, event):
        defCatId = event.attrs['n']
        self.defCats[defCatId] = []
        self.currentDefCat = self.defCats[defCatId]
        self.printDebugMessage("handle_def_cat_start", event)
        
    def handle_def_cat_end(self, event):
        self.currentDefCat = None
        self.printDebugMessage("handle_def_cat_end")
        
    def handle_cat_item_start(self, event):
        catItem = ''
        if 'lemma' in event.attrs:                  #lemma attribute is optional
            lemma = event.attrs['lemma']
            catItem = lemma
        
        for tag in event.attrs['tags'].split('.'):
            tag = "<{}>".format(tag)
            catItem += tag
        
        self.currentDefCat.append(catItem)
        self.printDebugMessage("handle_cat_item_start", event)
    
    def printDebugMessage(self, methodName, event=None):
        if (not event):
            self.logger.debug("{}()".format(methodName))
        else:
            self.logger.debug("{}: (<{} {}>)".format(methodName, event.name, event.attrs))
