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
import sys

class Debugger:
    """This class encapsulates all debugger logic."""

    def __init__(self, vm, interpreter):
        self.interpreter = None
        self.breakpoints = []
        self.breakOnRule = False
        self.step = False
        self.lastCommand = ""
        self.startLine = 0

        #Components used by the debugger.
        self.vm = vm
        self.interpreter = interpreter

    def start(self):
        """Start the debugger showing the message and ask for a command."""

        #If the input was a shell redirection, we need to reopen the terminal
        #to read the user commands.
        if not sys.stdin.isatty(): sys.stdin = open("/dev/tty")

        print()
        print("Apertium transfer VM debugger")
        print("The vm has been successfully initialized and all patterns and")
        print("the program code are loaded.")
        print("Type 'help' for a list of commands.")
        print()

        self.getCommand()

    def getCommand(self):
        """Get the user command and execute its appropiate method."""

        try:
            command = input("(vmdb) ")

            if command == "": command = self.lastCommand
            else: self.lastCommand = command

            command = command.strip().split(' ')
            cmd = command[0]
            args = command[1:]
            if cmd in ('h', 'help'): self.commandHelp(args)
            elif cmd in ('q', 'quit'): self.commandQuit()
            elif cmd in ('br', 'break'): self.commandBreak(args)
            elif cmd in ('c', 'continue'): self.commandContinue()
            elif cmd in ('d', 'delete'): self.commandDelete(args)
            elif cmd in ('i', 'info'): self.commandInfo(args)
            elif cmd in ('l', 'list'): self.commandList(args)
            elif cmd in ('p', 'print'): self.commandPrint(args)
            elif cmd in ('r', 'run'): self.commandRun()
            elif cmd in ('s', 'step'): self.commandStep()
            else:
                print("unknown command: '{}'. Try 'help'.".format(cmd))
                self.getCommand()
        except KeyboardInterrupt:
            self.commandQuit()

    def commandHelp(self, args):
        if len(args) == 0: self.showDebuggerHelp()
        else: self.showCommandHelp(args[0])

        self.getCommand()

    def commandQuit(self):
        self.vm.status = VM_STATUS.HALTED

    def commandBreak(self, args):
        if len(args) == 0 or args[0] == "onrule":
            self.breakOnRule = True
            print("Set breakpoint by default when a new rule starts.")
        elif args[0].isnumeric():
            codeLine = args[0]
            self.breakpoints.append(int(codeLine))
            print("Set breakpoint at {} line.".format(codeLine))

        self.getCommand()

    def commandContinue(self):
        pass

    def commandDelete(self, args):
        if len(args) == 0:
            answer = ''
            while answer != 'y' and answer != 'n':
                answer = input("Do you want to delete all breakpoints? (y o n) ")
            if answer == 'y':
                self.breakOnRule = False
                self.breakpoints = []
        elif args[0].isnumeric():
            breakPos = int(args[0])
            del self.breakpoints[breakPos]
        elif args[0] == "onrule": self.breakOnRule = False

        self.getCommand()

    def commandInfo(self, args):
        if len(args) == 0: pass
        elif args[0] in ('br', 'breakpoints'):
            if self.breakOnRule: print("Breakpoint on rule start")
            if len(self.breakpoints) > 0:
                print("{}\t {}".format("Num", "Line"))
                for n, br in enumerate(self.breakpoints):
                    print("{}\t {}".format(n, br))
        elif args[0] in ('st', 'stack'):
            print(self.vm.stack)

        self.getCommand()

    def commandList(self, args):
        loader = self.vm.loader

        #If an argument is supplied, show lines around it.
        if len(args) == 1:
            line = int(args[0])
            if line > 5: self.startLine = line - 5
            else: self.startLine = 0
            endLine = line + 5
        else: endLine = self.startLine + 10

        for line in range(self.startLine, endLine):
            try:
                loader.printInstruction(self.vm.currentCodeSection[line], line)
            except IndexError:
                break
        self.startLine = endLine

        self.getCommand()

    def commandPrint(self, args):
        if len(args) == 0: pass
        elif args[0] == "variables":
            print(self.vm.variables)
        else:
            varName = args[0]
            try:
                print("{} = '{}'".format(varName, self.vm.variables[varName]))
            except KeyError:
                print("Variable '{}' doesn't exists, maybe it hasn't been "
                      "initialized".format(varName))

        self.getCommand()

    def commandRun(self):
        pass

    def commandStep(self):
        self.step = True

    def showDebuggerHelp(self):
        print("List of commands available (abbreviation and full command):")
        print()
        print("br, break: to set a breakpoint")
        print("c, continue: continue execution until a breakpoint or the end")
        print("d, delete: delete all breakpoints or the indicated one")
        print("i, info: show some info about the vm and its current state")
        print("l, list: list code ten lines by ten lines")
        print("p, print: print the value of a variable")
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
        elif cmd in ('br', 'break'):
            print("break [N | onrule]")
            print("\t 'break' by default will set a breakpoint on rule start")
            print("\t 'break N' will set a breakpoint at line N")
            print("\t 'break onrule will set a breakpoint at rule start")
        elif cmd in ('c', 'continue'):
            print("c, continue: continue execution until a breakpoint or the end")
        elif cmd in ('d', 'delete'):
            print("delete [N | onrule]:")
            print("\t 'delete' will delete all current breakpoints")
            print("\t 'delete N' will delete the number N breakpoint")
            print("\t 'delete onrule' will delete the breakpoint on rule start")
        elif cmd in ('i', 'info'):
            print("info [breakpoints | stack]:")
            print("\t 'info breakpoints' will show every current breakpoint")
            print("\t 'info stack' will show the system stack content")
        elif cmd in ('l', 'list'):
            print("list [line]")
            print("\t 'list' will show ten lines of code each time")
            print("\t [line] list ten lines around line")
        elif cmd in ('p', 'print'):
            print("print [variables | variableName]:")
            print("\t 'print variables' will print all the variables and their "
                  "values")
            print("\t 'print variableName' will print the variable value")
        elif cmd in ('s', 'step'):
            print("s, step: execute the next line and stop")
        elif cmd in ('r', 'run'):
            print("r, run: execute the current loaded program")
        else: print("unknown command: '{}'. Try 'help'.".format(cmd))

    def execute(self, instr):
        PC = self.vm.PC
        if self.step:
            self.step = False
            print()
            self.vm.loader.printInstruction(instr, PC)
            self.getCommand()
        elif PC in self.breakpoints:
            print()
            self.vm.loader.printInstruction(instr, PC)
            self.getCommand()
        self.interpreter.execute(instr)

    def preprocess(self):
        self.interpreter.preprocess()

    def ruleSelected(self, pattern, ruleNumber):
        self.startLine = 0

        if self.breakOnRule:
            print('\nPattern "{}" match rule: {}\n'.format(pattern, ruleNumber))
            self.getCommand()
