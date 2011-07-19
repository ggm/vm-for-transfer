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

"""This modules contains some of the constants used through all the vm."""

class VM_STATUS:
    """Represents the state of the vm as a set of constants."""

    RUNNING = 0
    HALTED = 1
    FAILED = 2

class TRANSFER_STAGE:
    """Represents the current stage of the transfer system."""

    CHUNKER = 0
    INTERCHUNK = 1
    POSTCHUNK = 2

class CHUNKER_MODE:
    """Represents the default behavior in the chunker stage."""

    CHUNK = 0
    LU = 1