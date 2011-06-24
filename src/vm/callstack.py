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

class CallStack:
    """This class represents a stack of different code sections."""

    def __init__(self, vm):
        #Access to the data structures of the vm is needed.
        self.vm = vm

        #The actual stack used to track the calls and returns.
        self.stack = []

    def push(self, section, number, PC=0):
        """Push a code section in the call stack. This is needed because a rule
           can call a macro and a macro can also call a macro, so storing the
           last PC isn't enough, we also need the code section.
        """

        self.stack.append({'section' : section, 'number' : number,
                               'PC' : PC})
        self.setCurrentSection(section, number, PC)

    def pop(self):
        """Pop the current code section and set the last one as the current one.
           This is done when a macro ends, it restores its caller and its PC.
        """

        self.stack.pop()
        call = self.stack[-1]
        self.setCurrentSection(call['section'], call['number'], call['PC'])

    def setCurrentSection(self, section, number, PC):
        """Set the current section as the one passed as parameters."""

        self.vm.PC = PC
        n = number
        if section == "rules":
            self.vm.currentCodeSection = self.vm.rulesCode[n]
        elif section == "macros":
            self.vm.currentCodeSection = self.vm.macrosCode[n]

    def saveCurrentPC(self):
        """Save the current PC so we can return to it and the end of a call."""

        currentSection = self.stack.pop()
        currentSection['PC'] = self.vm.PC
        self.stack.append(currentSection)
