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

"""
This module serves as a change only once place and contains the internal
representation of the instructions used by the vm. All the others loaders and
interpreters should used this module to become immune to changes.
"""

class OpCodes:
    ADDTRIE = 0
    AND = 1
    APPEND = 2
    BEGINS_WITH = 3
    BEGINS_WITH_IG = 4
    OR = 5
    CALL = 6
    CLIP = 7
    CLIPSL = 8
    CLIPTL = 9
    CMP_SUBSTR = 10
    CMPI_SUBSTR = 11
    CMP = 12
    CMPI = 13
    CONCAT = 14
    CHUNK = 15
    ENDS_WITH = 16
    ENDS_WITH_IG = 17
    GET_CASE_FROM = 18
    IN = 19
    INIG = 20
    JMP = 21
    JZ = 22
    JNZ = 23
    MLU = 24
    MODIFY_CASE = 25
    PUSH = 26
    PUSHBL = 27
    PUSHSB = 28
    LU = 29
    LU_COUNT = 30
    NOT = 31
    OUT = 32
    RET = 33
    STORECL = 34
    STORESL = 35
    STORETL = 36
    STOREV = 37
