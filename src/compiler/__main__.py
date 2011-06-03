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
USAGE: compiler [-d] [-i input_file] [-o output_file] [-h] 
Options:
  -d, --debug:\t\t show debug messages
  -i, --inputfile:\t input file (stdin by default)
  -o, --outputfile:\t output file (stdout by default)
  -h, --help:\t\t show this help
"""

import sys
import getopt
from compiler import Compiler
import logging

def showHelp():
    print(__doc__.strip())
    
def exit():
    showHelp()
    sys.exit(2)

def main():
    #Configure the logging module with a custom format.
    logging.basicConfig(format=('%(levelname)s: %(filename)s[%(lineno)d]:\t%(message)s'))
    compiler = Compiler()

    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "di:o:h", ["debug", "inputfile=", "outputfile=", "help"])
    except getopt.GetoptError as error:
        print(error)          
        exit()                     
    #Go through the options, initializing and configuring the compiler.    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            exit()                
        elif opt in ('-d', '--debug'):
            compiler.logger.setLevel(logging.DEBUG)
        elif opt in ("-i", "--inputfile"):
            try:
                compiler.input = open(arg, mode='rt', encoding='utf-8')
            except IOError as ioe:
                print(ioe)
                sys.exit(2)
        elif opt in ("-o", "--outputfile"):
            try:
                compiler.output = open(arg, mode='wb')
            except IOError as ioe:
                print(ioe)
                sys.exit(2)

    #compiler.output.write(compiler.input.read())
    compiler.compile()
    
    sys.exit(0)

if __name__ == '__main__':
    main()

