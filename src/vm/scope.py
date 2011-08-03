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

class Scope:
    """This class represents a scope in the assembly and vm."""

    def __init__(self):
        #Next executable address, used to set the labels to an address.
        self.nextAddress = 0
        #Each label is converted to an internal address of the vm.
        self.labelAddress = {}
        #Store the labels in need of backpatching.
        self.patchNeeded = {}

    def addLabelToPatch(self, label, pos):
        """Add a reference to an unknown label, to later patch it."""

        if label in self.patchNeeded: self.patchNeeded[label].append(pos)
        else: self.patchNeeded[label] = [pos]

    def backPatchLabels(self, section):
        """Backpatch all the labels with require it."""

        for label in self.patchNeeded:
            address = str(self.labelAddress[label])
            for pos in self.patchNeeded[label]:
                instr = section[pos][1]
                instr = instr.replace("#0#", address)
                section[pos][1] = instr


    def createNewLabelAddress(self, label):
        """Create a new unique internal address for a label."""

        labelAddress = self.nextAddress
        self.labelAddress[label] = labelAddress
        return labelAddress

    def getReferenceToLabel(self, label, section):
        """Get the label address if it's already processed or mark it as patch
           needed if the label address is unknown yet.
        """

        if label in self.labelAddress: return self.labelAddress[label]
        else:
            self.addLabelToPatch(label, len(section))
            return "#0#"
