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
    JMP_OP = "jmp"          #jmp label -> jumps to the label, unconditionally.

    def __init__(self):
        self.logger = logging.getLogger('compiler')

        #The code we are going to generate.
        self.code = []

        #Used to get the next address of an instruction if needed.
        self.nextAddress = 0

    def genTransferStart(self, event):
        #Jump to the start of the rules, ignoring the macros until called.
        self.code.append(self.JMP_OP + " section_rules_start")

    def genTransferEnd(self, event):
        self.code.append("section_rules_end:\n")
