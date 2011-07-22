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
import sys

class TransferLexicalUnit:
    """Represent a lexical unit and all its attributes for the transfer stage."""

    def __init__(self):
        self.lu = ""
        self.attrs = {}

        #Index of the first tag '<' character.
        self.tagStart = None

    def modifyAttr(self, attr, value):
        """Modify the part of the full lexical unit and the attr."""

        if attr == 'whole': self.setAttributes(value)
        else:
            if attr == 'tags':
                self.lu = self.lu.replace(self.attrs[attr], value)
            else:
                #Only modify the lu until the tags.
                self.lu = self.lu[:self.tagStart].replace(self.attrs[attr],
                          value) + self.lu[self.tagStart:]

            if attr == 'lem' or attr == 'lemh':
                #If the lemh is the same as the lem, we update both.
                if self.attrs['lem'] == self.attrs['lemh']:
                    self.attrs['lem'] = value
                    self.attrs['lemh'] = value
                    return

            self.attrs[attr] = value

    def modifyTag(self, tag, value):
        """Modify the tag of the full lexical unit and the attr."""

        #Only modify the tags and not the entire lu.
        self.lu = self.lu[:self.tagStart] \
                  + self.lu[self.tagStart:].replace(tag, value)
        self.attrs["tags"] = self.attrs["tags"].replace(tag, value)

    def setAttributes(self, token):
        """Set some of the attributes of a transfer lexical unit."""

        self.lu = token
        #Get the position of the key characters.
        tag = token.find('<')
        self.tagStart = tag
        head = token.find('#')

        if tag > -1:
            #Set tags depending on if the '#' is before or after tags.
            if head < tag:
                self.attrs['lem'] = token[:tag]
                self.attrs['tags'] = token[tag:]
            else:
                self.attrs['lem'] = token[:tag] + token[head:]
                self.attrs['tags'] = token[tag:head]
        else:
            #If there isn't any tag, the lemma is everything.
            self.attrs['lem'] = token
            self.attrs['tags'] = ""

        if head > -1:
            #Set lemh, lemq depending on if the '#' is before or after tags.
            if head < tag:
                self.attrs['lemh'] = token[:head]
                self.attrs['lemq'] = token[head:tag]
            else:
                self.attrs['lemh'] = token[:tag] 
                self.attrs['lemq'] = token[head:]
        #If it isn't a multiword, then the lemh is the lemma.
        else: self.attrs['lemh'] = self.attrs['lem']

class TransferWord:
    """Represent a word as a source/target language pair."""

    def __init__(self):
        self.source = TransferLexicalUnit()
        self.target = TransferLexicalUnit()

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
        escapeNextChar = False

        word = TransferWord()
        for char in input:
            if char == "\\": escapeNextChar = True
            elif escapeNextChar:
                token += str(char)
                escapeNextChar = False
            elif char == '^':
                #If there aren't any blanks at the beginning, append an empty.
                if len(tokens) == 0 and len(superblanks) == 0:
                    superblanks.append(token)
                #Any character, between lus, is treated like a superblank.
                elif len(tokens) == len(superblanks):
                    superblanks.append(token)
                #If there are characters after the superblank, append them.
                elif token != "":
                    superblanks.append(superblanks.pop() + token)
                token = ""
            elif char == '$':
                word.target.setAttributes(token.strip())
                tokens.append(word)
                token = ""
                word = TransferWord()
            elif char == '/':
                word.source.setAttributes(token.strip())
                token = ""
            elif char == '[':
                #If there are characters before the superblank, append them.
                if token != "":
                    sb += token
                    token = ""
                insideSb = True
            elif char == ']':
                if sb != "": superblanks.append(sb)
                insideSb = False
                sb = ""
            elif insideSb: sb += str(char)
            else: token += str(char)

        return tokens, superblanks

class ChunkLexicalUnit:
    """Represent a lexical unit and all its attributes for the inter/postchunk."""

    def __init__(self):
        self.lu = ""
        self.attrs = {}

        #Index of the first tag '<' character.
        self.tagStart = None
        #Index of the first '{', the start of the chunk content.
        self.contentStart = None

    def modifyAttr(self, attr, value):
        """Modify the part of the full lexical unit and the attr."""

        if attr == 'whole': self.setAttributes(value)
        else:
            if attr == 'tags':
                self.lu = self.lu.replace(self.attrs[attr], value)
            elif attr == 'chcontent':
                chcontent = self.attrs[attr]
                lu = self.lu[:self.contentStart]
                lu += self.lu[self.contentStart:].replace(chcontent, value)
                self.lu = lu
            else:
                #Only modify the lu until the tags.
                self.lu = self.lu[:self.tagStart].replace(self.attrs[attr],
                          value) + self.lu[self.tagStart:]
                self.attrs[attr] = value

    def modifyTag(self, tag, value):
        """Modify the tag of the full lexical unit and the attr."""

        #Only modify the tags and not the entire lu.
        self.lu = self.lu[:self.tagStart] \
                + self.lu[self.tagStart:self.contentStart].replace(tag, value) \
                + self.lu[self.contentStart:]
        self.attrs["tags"] = self.attrs["tags"].replace(tag, value)
            
    def setAttributes(self, token):
        """Set some of the attributes of a chunk lexical unit."""

        #Get the position of the key characters.
        self.lu = token
        tag = token.find('<')
        self.tagStart = tag
        contentStart = token.find('{')
        self.contentStart = contentStart
        contentEnd = token.find('}')

        if tag > -1:
            #The lemma is everything until the first tag.
            self.attrs['lem'] = token[:tag]
            self.attrs['tags'] = token[tag:contentStart]
        else:
            #If there isn't any tag, the lemma is everything until the '{'.
            self.attrs['lem'] = token[:contentStart]
            self.attrs['tags'] = ""

        #Store chunk contents with the '{' and '}'.
        self.attrs['chcontent'] = token[contentStart:contentEnd + 1]

class ChunkWord:
    """Represent a word as a chunk for the interchunk and postchunk stages."""

    def __init__(self):
        self.chunk = ChunkLexicalUnit()
        self.content = []
        self.blanks = []

    def __str__(self):
        string = "^{}$: {}, content = [ ".format(self.chunk.lu, self.chunk.attrs)
        for lu in self.content:
            string += "^{}$: {} ".format(lu.lu, lu.attrs)
        string += ']'

        return string

    def parseChunkContent(self):
        """Set the content of the chunk word as a list of lexical units
           and apply the postchunk rule of setting the case of the lexical
           units as the one of the chunk pseudolemma.
        """

        #Depending on the case, change all cases or just the first lexical unit.
        pseudoLemmaCase = self.getCase(self.chunk.attrs['lem'])
        upperCaseAll = False
        firstUpper = False
        if pseudoLemmaCase == "AA": upperCaseAll = True
        elif pseudoLemmaCase == "Aa": firstUpper = True

        content = []
        #The first blank (0) is the one before the chunk name.
        blanks = [""]
        firstLu = True
        chcontent = self.chunk.attrs['chcontent'][1:-1] #Remove { and }.

        for token in chcontent.split('$'):
            if len(token) < 2: continue

            #After the first blank, append the blanks between lexical units.
            if firstLu: firstLu = False
            else: blanks.append(token[:token.find('^')])

            lu = TransferLexicalUnit()
            lu.setAttributes(token.replace('^', '').replace('/', '').strip())

            if upperCaseAll: self.changeLemmaCase(lu, pseudoLemmaCase)
            elif firstUpper:
                self.changeLemmaCase(lu, pseudoLemmaCase)
                firstUpper = False

            content.append(lu)

        self.content = content
        self.blanks = blanks

    def getCase(self, string):
        """Get the case of a string, defaulting to capitals."""

        isFirstUpper = string[0].isupper()
        isUpper = string.isupper()

        #If it's a 1-length string and is upper, capitalize it.
        if isUpper and len(string) == 1: return "Aa"
        elif isFirstUpper and not isUpper: return "Aa"
        elif isUpper: return "AA"
        else: return "aa"

    def changeLemmaCase(self, lu, case):
        """Change the case of the lemma in a lexical unit."""

        oldLu = lu.lu
        oldLem = lu.attrs['lem']
        if case == "aa": newLem = oldLem.lower()
        elif case == "Aa": newLem = oldLem.capitalize()
        elif case == "AA": newLem = oldLem.upper()
        lu.modifyAttr('lem', newLem)

        #Also, update the chcontent attribute of the chunk.
        chcontent = self.chunk.attrs['chcontent']
        self.chunk.attrs['chcontent'] = chcontent.replace(oldLu, lu.lu)

class ChunkWordTokenizer():
    """Create a set of chunk words from an input stream."""

    def __init__(self, solveRefs=False, parseContent=False):
        self.solveRefs = solveRefs
        self.parseContent = parseContent

    def tokenize(self, input):
        """Tokenize the input in ^name<tags>{^...$} tokens."""

        input = input.read()
        tokens = []
        token = ""
        superblanks = []
        chunkStart = True

        word = ChunkWord()
        for char in input:
            #Read the ^ and $ of the lexical units but not of the chunks.
            if char == '^':
                if not chunkStart: token += str(char)
                else:
                    #Characters between chunks are treated like superblanks.
                    superblanks.append(token)
                    token = ""
                    chunkStart = False
            elif char == '$':
                if not chunkStart: token += str(char)
            elif char == '}':
                token += str(char)
                word.chunk.setAttributes(token.strip())
                if self.solveRefs: self.solveReferences(word)
                if self.parseContent: word.parseChunkContent()
                tokens.append(word)
                #Initialize auxiliary variables.
                chunkStart = True
                token = ""
                word = ChunkWord()
            else: token += str(char)

        #Append the last superblank of the input, usually the '\n'.
        superblanks.append(token)

        return tokens, superblanks

    def solveReferences(self, word):
        """Solve the references to the chunk tags."""

        tags = word.chunk.attrs['tags']
        tags = tags.replace('<', '')
        tags = tags.split('>')
        lu = word.chunk.lu
        chcontent = word.chunk.attrs['chcontent']
        newChcontent = chcontent

        for i, char in enumerate(chcontent):
            if char.isnumeric():
                if chcontent[i - 1] == '<' and chcontent[i + 1] == '>':
                    pos = int(char)
                    tag = tags[pos - 1]
                    lu = self.replaceReference(lu, char, tag)
                    newChcontent = self.replaceReference(newChcontent, char, tag)

        word.chunk.lu = lu
        word.chunk.attrs['chcontent'] = newChcontent

    def replaceReference(self, container, pos, tag):
        """Replace a number (pos) with the tag in the container."""

        for i, char in enumerate(container):
            if char == pos:
                if container[i - 1] == '<' and container[i + 1] == '>':
                    newContainer = container[:i] + tag + container[i + 1:]

        return newContainer
