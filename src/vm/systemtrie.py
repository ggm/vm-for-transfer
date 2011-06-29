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

    def getPatternNode(self, pattern, startNode=None):
        """Get the last node of the sequence representing the pattern."""

        if not pattern: return None

        if startNode: curNode = startNode
        else: curNode = self.root

        for char in pattern:
            try:
                curNode = curNode.children[char]
            except KeyError:
                return None

        return curNode

    def getRuleNumber(self, pattern):
        """Get the rule number for a given pattern."""

        curNode = self.getPatternNode(pattern)

        if curNode: return curNode.ruleNumber
        else: return None

    def addPattern(self, pattern, ruleNumber):
        #One string will be processed by character and a list by part.
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
        curNodes = [self.root]
        for part in pattern[:-1]:
            lastNodes = []
            for node in curNodes:
                if '|' in part:
                    for option in part.split('|'):
                        lastNodes.append(self._insertPattern(option, node=node))
                else:
                    lastNodes.append(self._insertPattern(part, node=node))
            curNodes = lastNodes

        #Finally, we add the last part of the pattern with its rule number.
        lastPart = pattern[-1]
        for node in curNodes:
            self._insertPattern(lastPart, ruleNumber, node)

    def _insertPattern(self, pattern, ruleNumber=None, node=None):
        """Internal method used only by this class to insert part of a
           pattern, starting in a node passed as argument.
        """

        if not node: curNode = self.root
        else: curNode = node

        for char in pattern:
            curNode = curNode.children.setdefault(char, TrieNode())
        curNode.ruleNumber = ruleNumber

        return curNode

if __name__ == '__main__':
    #Some tests for reference.
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
        actual = trie.getRuleNumber(key)
        if actual != expected:
            print("Error: {} is {}, not {}".format(key, actual, expected))
        else:
            print("Test Ok: {} is {}".format(key, actual))

    #Test when there isn't a pattern.
    actual = trie.getRuleNumber("<nonexsitent>")
    if not actual:
        print("Test Ok: nonexistent pattern")
    else:
        print("Error: nonexistent pattern exists as {}".format(actual))

    #Test the option parts.
    pattern = ["<det><nom>", "<adj>|<adj><sint>|<adj><comp>|<adj><sup>", "<adv_pp>"]
    trie.addPattern(pattern, 40)

    testOptions = {"<det><nom><adj><adv_pp>" : 40,
                   "<det><nom><adj><sint><adv_pp>" : 40,
                   "<det><nom><adj><comp><adv_pp>" : 40,
                   "<det><nom><adj><sup><adv_pp>" : 40
                   }

    for key, expected in testOptions.items():
        actual = trie.getRuleNumber(key)
        if actual != expected:
            print("Error: {} is {}, not {}".format(key, actual, expected))
        else:
            print("Test Ok: {} is {}".format(key, actual))
