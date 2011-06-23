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

class TransferWord:
    """Represent a word as a source/target language pair."""

    def __init__(self):
        self.source = ""
        self.target = ""

    def __str__(self):
        return "^{}/{}$".format(self.source, self.target)

class TransferWordTokenizer():
    """Create a set of transfer words from an input stream."""

    def __init__(self):
        pass

    def tokenize(self, input):
        """Tokenize the input in ^...$ tokens."""

        input = input.read()
        tokens = []
        token = ""

        word = TransferWord()
        for char in input:
            if char == '^': pass
            elif char == '$':
                word.target = token.strip()
                tokens.append(word)
                token = ""
                word = TransferWord()
            elif char == '/':
                word.source = token.strip()
                token = ""
            else: token += str(char)

        return tokens
