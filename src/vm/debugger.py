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

from constants import VM_STATUS

class Debugger:
    """This class encapsulates all debugger logic."""

    def __init__(self, vm, interpreter):
        self.interpreter = None
        self.breakpoints = []
        self.breakOnRule = False

        #Components used by the debugger.
        self.vm = vm
        self.interpreter = interpreter

    def start(self):
        """Start the debugger showing the message and ask for a command."""

        print()
        print("Apertium transfer VM debugger")
        print("The vm has been successfully initialized and all patterns and")
        print("the program code are loaded.")
        print("Type 'help' for a list of commands.")
        print()

        self.getCommand()

    def getCommand(self):
        """Get the user command and execute its appropiate method."""

        command = input("(vmdb) ")
        command = command.strip().split(' ')

        cmd = command[0]
        args = command[1:]
        if cmd in ('h', 'help'): self.commandHelp(args)
        elif cmd in ('q', 'quit'): self.commandQuit()
        elif cmd in ('r', 'run'): self.commandRun()
        else:
            print("unknown command: '{}'. Try 'help'.".format(cmd))
            self.getCommand()

    def commandHelp(self, args):
        if len(args) == 0: self.showDebuggerHelp()
        else: self.showCommandHelp(args[0])

        self.getCommand()

    def commandQuit(self):
        self.vm.status = VM_STATUS.HALTED

    def commandRun(self):
        pass

    def showDebuggerHelp(self):
        print("List of commands available (abbreviation and full command):")
        print("br, break: to set a breakpoint")
        print("i, info: show some info about the vm and its current state")
        print("r, run: execute the current loaded program")
        print("s, step: execute the next line and stop")
        print("h, help: show this help")
        print("q, quit: quit the debugger")
        print()
        print("Type 'help' followed by a command name for more information.")
        print()

    def showCommandHelp(self, cmd):
        if cmd in ('h', 'help'): self.showDebuggerHelp()
        elif cmd in ('q', 'quit'): print("q, quit: quit the debugger")
        elif cmd in ('r', 'run'):
            print("r, run: execute the current loaded program")
        else: print("unknown command: '{}'. Try 'help'.".format(cmd))

    def execute(self, instr):
        self.interpreter.execute(instr)

    def preprocess(self):
        self.interpreter.preprocess()

    def ruleSelected(self, pattern, ruleNumber):
        print('Pattern "{}" match rule: {}'.format(pattern, ruleNumber))
        if self.breakOnRule: self.getCommand()
