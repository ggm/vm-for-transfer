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
from compilererror import CompilerError

class Symbol:
    """Stores all the necessary information about symbols."""

    #Define the different types of symbols.
    TYPE_MACRO = 0
    
    def __init__(self, id, name, numParams, type):
        self.id = id
        self.name = name
        self.numParams = numParams
        self.type = type
        
    def typeToStr(self):
        if self.type == 0: return "Macro"

class SymbolTable:
    """Represents a collection of symbols."""

    def __init__(self):
        #Store symbols in a dictionary with their name as key.
        self.symbols = {}
        #Each symbol has a unique id (order by appearance on the rules files).
        self.nextId = 0
        
    def __addSymbol(self, name, numParams, type):
        id = self.nextId
        self.nextId += 1
        s = Symbol(id, name, numParams, type)
        self.symbols[name] = s
        
    def addMacro(self, name, numParams):
        if name in self.symbols:
            raise CompilerError("Macro '{}' already defined".format(name))
        self.__addSymbol(name, numParams, Symbol.TYPE_MACRO)
        
    def __str__(self):
        """Print a readable version of the symbol table for debugging purposes."""
        size = 60
        halfSize = int(size/2)
        contentsFormat = "|{:^10}|{:^23}|{:^10}|{:^14}|\n"
        border = '+' + '-' * size + '+' + '\n'
        
        string ='\n\n'
        string += border
        string +=  '|' + ' ' * (halfSize - 6) + "Symbol Table" + ' ' * (halfSize - 6) + '|\n'
        string += border
        string += contentsFormat.format("Id", "Name", "Nº par", "Type")
        string += border

        #Print symbol table sorted by ID.        
        sortedValues = sorted(self.symbols.values(), key = lambda symbol: symbol.id)
        for s in sortedValues:
            string += contentsFormat.format(s.id, s.name, s.numParams, s.typeToStr())
        string += border
        
        return string