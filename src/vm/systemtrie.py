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

class TrieNode:
    """This class represents a node of the trie data structure."""

    def __init__(self):
        #The rule's number to apply, if it's the end of a pattern.
        self.ruleNumber = None
        #A collection of children with the next character as key.
        self.children = {}

    def addChild(self, key, nextNode):
        self.children[key] = nextNode

class SystemTrie:
    """
    This class stores the patterns, used to identify which rules to apply, as
    a trie for easy retrieval.
    """

    def __init__(self):
        self.root = TrieNode()

    def __getNextNodes(self, char, startNode):
        """Get a list of next nodes given a char and a start node."""

        nextNodes = []
        if char.isalpha() and '*' in startNode.children:
            nextNodes.append(startNode.children['*'])

        try:
            nextNodes.append(startNode.children[char])
        except KeyError:
            pass

        return nextNodes

    def __insertPattern(self, pattern, ruleNumber=None, node=None):
        """Internal method used only by this class to insert part of a
           pattern, starting in a node passed as argument.
        """

        if not node: curNode = self.root
        else: curNode = node

        for char in pattern:
            if char == '*': curNode = self.__insertTagStar(curNode)
            else: curNode = curNode.children.setdefault(char, TrieNode())

        #If a pattern already exists, keep the first rule on the rule's file.
        if ruleNumber is not None:
            if curNode.ruleNumber is None: curNode.ruleNumber = ruleNumber
            else: curNode.ruleNumber = min(curNode.ruleNumber, ruleNumber)

        return curNode

    def __insertStar(self, node):
        """Insert a star node which can contain any alphabetic character."""

        #If there is already a tag star, create a new different star node,
        #so that it does not eat every consequent lemma<tag>.
        if '<' in node.children and '*' in node.children['<'].children:
            node = node.children.setdefault('*', TrieNode())

        #Add a reference to itself to accept every alphabet char.
        node.addChild('*', node)

        return node

    def __insertTagStar(self, node):
        """Insert a <*> to get a series of tags."""

        #Insert the star node following the last one.
        node = node.children.setdefault('*', TrieNode())
        #Add a reference to itself to accept every alphabet char.
        node.addChild('*', node)
        starNode = node
        #Add the end and the start of a possible next tag.
        node = node.children.setdefault('>', TrieNode())
        node = node.children.setdefault('<', TrieNode())
        #Add the reference to the star node and the cycle is complete.
        node.addChild('*', starNode)

        return starNode

    def getPatternNodes(self, pattern, startNode=None):
        """Get the last nodes of the sequence representing the pattern."""

        if not pattern: return None

        if startNode: curNodes = [startNode]
        else: curNodes = [self.root]

        for char in pattern:
            nextNodes = []
            for node in curNodes:
                nextNodes.extend(self.__getNextNodes(char, node))
            curNodes = nextNodes
            if len(curNodes) == 0: return None

        return curNodes

    def getRuleNumber(self, pattern):
        """Get the rule number for a given pattern."""

        curNodes = self.getPatternNodes(pattern)

        if curNodes:
            try:
                #If there are several possible rules, return the first which
                #appears on the rules file.
                return min(node.ruleNumber
                                for node in curNodes 
                                if node.ruleNumber is not None)
            except ValueError: return None
        else: return None

    def addPattern(self, pattern, ruleNumber):
        """Add a pattern, as a string or a list of strings, to the trie."""

        #Convert the pattern to a list if it's just a string.
        if not isinstance(pattern, list): pattern = [pattern]

        #Firstly we add all the parts of the pattern but the last one. Options
        #are stored in a list of curNodes and the next part is inserted after
        #each option, for example, given the input:
        #
        # Pattern: ["<det><nom>", "<adj>|<adj><sint>|<adj><comp>", "<adv_pp>"]
        # Rule number: 12
        #
        # The output trie would be:
        #                            /~~<adv_pp> -> 12
        #                           |
        #        <det><nom>~~<adj>~~|~~<sint>~~<adv_pp> -> 12
        #                           |
        #                            \~~<comp>~~<adv_pp> -> 12
        #
        # Note: if a pattern starts directly with tags, we need to add a node
        # for every alphabetic char (*), so it can accept patterns with lemmas.
        
        curNodes = [self.root]
        for part in pattern[:-1]:
            lastNodes = []
            for node in curNodes:
                if '|' in part:
                    for option in part.split('|'):
                        if option[0] == '<': node = self.__insertStar(node)
                        lastNodes.append(self.__insertPattern(option, node=node))
                else:
                    if part[0] == '<': node = self.__insertStar(node)
                    lastNodes.append(self.__insertPattern(part, node=node))
            curNodes = lastNodes

        #Finally, we add the last part of the pattern with its rule number.
        lastPart = pattern[-1]
        for node in curNodes:
            if '|' in lastPart:
                for option in lastPart.split('|'):
                    if option[0] == '<': node = self.__insertStar(node)
                    self.__insertPattern(option, ruleNumber, node=node)
            else:
                if lastPart[0] == '<': node = self.__insertStar(node)
                self.__insertPattern(lastPart, ruleNumber, node=node)

    def printTrie(self):
        """Print trie's contents and structure just for debugging purposes."""

        self.ids = {}
        self.nextId = -1
        self.visitedNodes = {}
        self.__printNode(self.root)

    def __printNode(self, node):
        """Print a trie node and all of its children (debugging purposes)."""

        if node in self.visitedNodes: return
        else: self.visitedNodes[node] = True

        print("Node #{}: rule={}, children ="
              .format(self.__getNodePrintableId(node), node.ruleNumber), end='')
        string = ""
        for char in node.children:
            string += " '{}' -> {}" \
            .format(char, self.__getNodePrintableId(node.children[char]))
        print(string)

        for char in node.children:
            self.__printNode(node.children[char])

    def __getNodePrintableId(self, node):
        """Get a printable ID for a trie node (debugging purposes)."""

        if node not in self.ids:
            self.nextId += 1
            self.ids[node] = self.nextId

        return self.ids[node]

if __name__ == '__main__':

    def testPattern(key, expected):
        actual = trie.getRuleNumber(key)
        if actual != expected:
            print("Error: {} is {}, not {}".format(key, actual, expected))
        else:
            print("Test Ok: {} is {}".format(key, actual))

    #Some tests for reference purposes.
    trie = SystemTrie()

    testDict = {"<det><nom><adj>" : 11, "<det><adj><nom>" : 12,
                "<det><adj><nom><adj>" : 13, "<det><nom><adj><adj>" : 14,
                "<num><nom><adj>" : 21, "<nom><num><adj>" : 22,
                "<nom><adj><adj>" : 23,
                "<adv_pp>" : 31, "<adv_pp><adj><adj>" : 32
                }
    #Add all the patterns with their rule's number.
    for key, value in testDict.items():
        trie.addPattern(key, value)
    #Test the retrieval of the trie.
    for key, expected in testDict.items():
        testPattern(key, expected)

    #Test when there isn't a pattern.
    testPattern("<nonexistent>", None)

    #Test the option parts.
    pattern = ["<det><nom>",
               "<adj>|<adj><sint>|<adj><comp>|<adj><sup>",
               "<adv_pp>"]
    trie.addPattern(pattern, 40)

    testOptions = {"<det><nom><adj><adv_pp>" : 40,
                   "<det><nom><adj><sint><adv_pp>" : 40,
                   "<det><nom><adj><comp><adv_pp>" : 40,
                   "<det><nom><adj><sup><adv_pp>" : 40
                   }
    for key, expected in testOptions.items():
        testPattern(key, expected)

    #Test that a pattern starting with tag is inserted as *<pattern>.
    patterns = ["all<predet><sp><n><pl>", "all<predet><sp>student<n><pl>"]
    expected = 50
    trie.addPattern(["all<predet><sp>", "<n><pl>"], expected)
    for key in patterns:
        testPattern(key, expected)

    #Test * inside tags.
    patterns = {"<n><sg><gen>" : None, "<n><m><sg><gen>" : None,
                "<n><m><sg><ND><gen>" : 55, "student<n><sp><sg><f><gen>" : 55,
                "<vblex>" : None, "<vblex><pp>" : 56, "<vblex><pron><pp>" : 56,
                "<pp><vblex>" : None, "<vblex><sep><past><pron><pp>" : 56
                }
    trie.addPattern("<n><*><sg><*><gen>", 55)
    trie.addPattern("<vblex><*>", 56)
    for key, expected in patterns.items():
        testPattern(key, expected)
