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

    def modifyAttr(self, attr, value):
        """Modify the part of the full lexical unit and the attr."""

        self.lu = self.lu.replace(self.attrs[attr], value)
        self.attrs[attr] = value

    def modifyTag(self, tag, value):
        """Modify the tag of the full lexical unit and the attr."""

        self.lu = self.lu.replace(tag, value)
        self.attrs["tags"] = self.attrs["tags"].replace(tag, value)

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
        superblanks = []
        sb = ""
        insideSb = False
        firstTag = True
        source = True

        word = TransferWord()
        for char in input:
            if char == '^': pass
            elif char == '$':
                word.target.lu = token.strip()
                self.setAttributes(word.target, token)
                tokens.append(word)
                #Initialize auxiliary variables.
                source = True
                firstTag = True
                token = ""
                word = TransferWord()
            elif char == '/':
                word.source.lu = token.strip()
                self.setAttributes(word.source, token)
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
            elif char == '[' or (insideSb and char != ']'):
                sb += char
                insideSb = True
            elif char == ']':
                sb += char
                if sb == "[]": superblanks.append("")
                else: superblanks.append(sb)
                insideSb = False
                sb = ""
            else: token += str(char)

        return tokens, superblanks

    def setAttributes(self, word, token):
        """Set some of the attributes of a transfer word."""

        tag = word.lu.find('<')
        head = word.lu.find('#')
        if head > -1: word.attrs['lemq'] = word.lu[head:tag]
        if tag > -1: word.attrs['tags'] = word.lu[tag:]
        #If there isn't any tag, the lemma is everything until the moment.
        if 'lem' not in word.attrs:
            word.attrs['lem'] = token.strip()
        #If it's not a multiword, then the lemh is the lemma.
        if 'lemh' not in word.attrs:
            word.attrs['lemh'] = word.attrs['lem']

class ChunkWord:
    """Represent a word as a chunk for the interchunk and postchunk stages."""

    def __init__(self):
        self.chunk = LexicalUnit()

    def __str__(self):
        return "^{}$: {}".format(self.chunk.lu, self.chunk.attrs)

class ChunkWordTokenizer():
    """Create a set of chunk words from an input stream."""

    def __init__(self):
        pass

    def tokenize(self, input):
        """Tokenize the input in ^name<tags>{^...$} tokens."""

        input = input.read()
        tokens = []
        token = ""
        superblanks = []
        sb = ""
        insideSb = False
        firstTag = True
        chunkStart = True

        word = ChunkWord()
        for char in input:
            #Read the ^ and $ of the lexical units but not of the chunks.
            if char == '^':
                if not chunkStart: token += str(char)
                else: chunkStart = False
            elif char == '$':
                if not chunkStart: token += str(char)
            elif char == '}':
                token += str(char)
                word.chunk.lu = token.strip()
                self.setAttributes(word.chunk)
                tokens.append(word)
                #Initialize auxiliary variables.
                chunkStart = True
                firstTag = True
                token = ""
                word = ChunkWord()
            elif firstTag and char == '<' :
                #The lemma is everything until the first tag.
                word.chunk.attrs['lem'] = token.strip()
                token += str(char)
                firstTag = False
            elif char == '[' or (insideSb and char != ']'):
                sb += char
                insideSb = True
            elif char == ']':
                sb += char
                if sb == "[]": superblanks.append("")
                else: superblanks.append(sb)
                insideSb = False
                sb = ""
            else: token += str(char)

        return tokens, superblanks

    def setAttributes(self, word):
        """Set some of the attributes of a transfer word."""

        #Get the position of the key characters.
        token = word.lu
        tag = token.find('<')
        contentsStart = token.find('{')
        contentsEnd = token.find('}') + 1

        #Initialize the attributes using the positions.
        word.attrs['tags'] = token[tag:contentsStart]
        #Store chunk contents without the '{' and '}'.
        word.attrs['chcontent'] = token[contentsStart + 1:contentsEnd - 1]
        #If there isn't any tag, the lemma is everything until the '{'.
        if 'lem' not in word.attrs:
            word.attrs['lem'] = token[:contentsStart]
        #If it's not a multiword, then the lemh is the lemma.
        if 'lemh' not in word.attrs:
            word.attrs['lemh'] = word.attrs['lem']
