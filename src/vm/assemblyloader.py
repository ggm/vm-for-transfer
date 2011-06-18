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

class AssemblyLoader:
    """
    Reads and loads assembly instruction from a file and converts them to
    the format used by the VM.
    """

    def __init__(self, vm, t1xFile):
        #Access to the data structures of the vm is needed.
        self.vm = vm
        self.data = t1xFile

        #We convert the macro's name to a numerical address, used for indexing.
        self.macroAddress = {}
        self.nextMacroAddress = -1

    def getNextMacroAddress(self):
        """Get a new unique address for a macro."""

        self.nextMacroAddress += 1
        return self.nextMacroAddress

    def load(self):
        """
        Load an assembly file and transform the instructions to the vm
        representation, substituting macro names for addresses.
        """

        currentSection = self.vm.code
        for line in self.data.readlines():
            #Ignore comments.
            if line[0] == '#': continue
            #Handle the contents of each rule.
            elif line.startswith('action'):
                #At the start, create a list which will contain the rule's code.
                if line.endswith('start:\n'):
                    ruleNumber = int(line[7])
                    currentSection = []
                #At the end, create an entry on the rules section with the code.
                elif line.endswith('end:\n'):
                    self.vm.rulesCode.insert(ruleNumber, currentSection)
                    currentSection = self.vm.code
            #Handle the contents of each macro.
            elif line.startswith('macro'):
                #At the start create a list which will contain the macro's code.
                if line.endswith('start:\n'):
                    macroName = line[6:line.rfind("_start")]
                    address = self.getNextMacroAddress()
                    self.macroAddress[macroName] = address
                    currentSection = []
                #At the end create an entry on the macros section with the code.
                elif 'end:' in line:
                    self.vm.macrosCode.insert(address, currentSection)
                    currentSection = self.vm.code
            else:
                currentSection.append(line)
