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
USAGE: vm -c code_file [-i input_file] [-o output_file] [-h]
Options:
  -c, --codefile:\t\t a [chunker|interchunk|postchunk] compiled rules file
  -i, --inputfile:\t input file (stdin by default)
  -o, --outputfile:\t output file (stdout by default)
  -h, --help:\t\t show this help
"""

import sys
import getopt
from vm import VM

def showHelp():
    print(__doc__.strip())

def exit():
    showHelp()
    sys.exit(2)

def main():
    vm = VM()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:i:o:h", ["codefile=", "inputfile=", "outputfile=", "help"])
    except getopt.GetoptError as error:
        print(error)
        exit()                     
    #Go through the options, initializing and configuring the vm.
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            exit()
        elif opt in ('-c', '--codefile'):
            try:
                codeFile = open(arg, mode='rt', encoding='utf-8')
                header = codeFile.readline()
                if not vm.setLoader(header, codeFile):
                    print("The header of the file {} is not recognized:".format(arg))
                    print(header)
                    sys.exit(2)

                transferHeader = codeFile.readline()
                vm.setTransferStage(transferHeader)
            except IOError as ioe:
                print(ioe)
                sys.exit(2)
        elif opt in ("-i", "--inputfile"):
            try:
                vm.input = open(arg, mode='rt', encoding='utf-8')
            except IOError as ioe:
                print(ioe)
                sys.exit(2)
        elif opt in ("-o", "--outputfile"):
            try:
                vm.output = open(arg, mode='wb')
            except IOError as ioe:
                print(ioe)
                sys.exit(2)

    vm.run()

    sys.exit(0)

if __name__ == '__main__':
    main()

