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

    def getRuleNumber(self, pattern):
        curNode = self.root

        for char in pattern:
            try:
                curNode = curNode.children[char]
            except KeyError as ke:
                raise(ke)

        return curNode.ruleNumber

    def addPattern(self, pattern, ruleNumber):
        curNode = self.root

        for char in pattern:
            curNode = curNode.children.setdefault(char, TrieNode())

        curNode.ruleNumber = ruleNumber

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
