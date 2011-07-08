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

class LexicalUnit:
    """Represent a lexical unit and all its attributes."""

    def __init__(self):
        self.lu = ""
        self.attrs = {}

class TransferWord:
    """Represent a word as a source/target language pair."""

    def __init__(self):
        self.source = LexicalUnit()
        self.target = LexicalUnit()

    def __str__(self):
        return "^{}/{}$: {}/{}".format(self.source.lu, self.target.lu,
                                       self.source.attrs, self.target.attrs)

class TransferWordTokenizer():
    """Create a set of transfer words from an input stream."""

    def __init__(self):
        pass

    def tokenize(self, input):
        """Tokenize the input in ^...$ tokens."""

        input = input.read()
        tokens = []
        token = ""
        firstTag = True
        source = True

        word = TransferWord()
        for char in input:
            if char == '^': pass
            elif char == '$':
                word.target.lu = token.strip()
                #Set the queue and tags attributes.
                tag = word.target.lu.find('<')
                head = word.target.lu.find('#')
                if head > -1: word.target.attrs['lemq'] = word.target.lu[head:tag]
                word.target.attrs['tags'] = word.target.lu[tag:]
                if 'lemh' not in word.target.attrs:
                    word.target.attrs['lemh'] = word.target.attrs['lem']
                tokens.append(word)
                #Initialize auxiliary variables.
                source = True
                firstTag = True
                token = ""
                word = TransferWord()
            elif char == '/':
                word.source.lu = token.strip()
                #Set the queue and tags attributes.
                head = word.source.lu.find('#')
                tag = word.source.lu.find('<')
                if head > -1: word.source.attrs['lemq'] = word.source.lu[head:tag]
                word.source.attrs['tags'] = word.source.lu[tag:]
                if 'lemh' not in word.source.attrs:
                    word.source.attrs['lemh'] = word.source.attrs['lem']
                #Initialize auxiliary variables.
                source = False
                firstTag = True
                token = ""
            elif firstTag and char == '<' :
                #The lemma is everything until the first tag.
                if source: word.source.attrs['lem'] = token.strip()
                else: word.target.attrs['lem'] = token.strip()
                token += str(char)
                firstTag = False
            elif char == '#':
                #The head is the part of the lemma until the '#' character.
                if source: word.source.attrs['lemh'] = token.strip()
                else: word.target.attrs['lemh'] = token.strip()
                token += str(char)
            else: token += str(char)

        return tokens
