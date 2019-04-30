import re
import sys
from error import *
from arg import Arg

class Instruction:
    opcode = None
    arg1 = None
    arg2 = None
    arg3 = None
    args = 0

    def __init__(self, xml):
        """ Extracts values from <instruction> XML element and performs lexical and syntax analysis """

        if "opcode" not in xml.attributes:
            err.exit_script(err.lexical_or_syntax)

        if len(xml.attributes) != 2:
            err.exit_script(err.lexical_or_syntax)

        self.opcode = xml.attributes["opcode"].value
        arg1 = xml.getElementsByTagName("arg1")
        arg2 = xml.getElementsByTagName("arg2")
        arg3 = xml.getElementsByTagName("arg3")

        arg1_found = False
        arg2_found = False
        arg3_found = False
        for arg in xml.childNodes:
            # Check for excessive text inside instruction element
            if arg.nodeType == arg.TEXT_NODE:
                if (not arg.nodeValue.isspace()):
                    err.exit_script(err.lexical_or_syntax)
            
            # Check for duplicite argN elements
            elif arg.nodeType == arg.ELEMENT_NODE:
                if arg.localName == "arg1":
                    if arg1_found == False:
                        arg1_found = True
                    else:
                        err.exit_script(err.lexical_or_syntax)
                elif arg.localName == "arg2":
                    if arg2_found == False:
                        arg2_found = True
                    else:
                        err.exit_script(err.lexical_or_syntax)
                elif arg.localName == "arg3":
                    if arg3_found == False:
                        arg3_found = True
                    else:
                        err.exit_script(err.lexical_or_syntax)
                else:
                    err.exit_script(err.lexical_or_syntax)

        if len(arg1) == 1:
            self.arg1 = Arg(arg1[0])
            self.args = 1 
        if len(arg2) == 1:
            self.arg2 = Arg(arg2[0])
            self.args = 2 
        if len(arg3) == 1:
            self.arg3 = Arg(arg3[0])
            self.args = 3

        if self.opcode == "CREATEFRAME" or \
           self.opcode == "PUSHFRAME" or \
           self.opcode == "POPFRAME" or \
           self.opcode == "RETURN" or \
           self.opcode == "BREAK" or \
           self.opcode == "CLEARS" or \
           self.opcode == "ADDS" or \
           self.opcode == "SUBS" or \
           self.opcode == "MULS" or \
           self.opcode == "IDIVS" or \
           self.opcode == "DIVS" or \
           self.opcode == "LTS" or \
           self.opcode == "GTS" or \
           self.opcode == "EQS" or \
           self.opcode == "ANDS" or \
           self.opcode == "ORS" or \
           self.opcode == "NOTS" or \
           self.opcode == "INT2CHARS" or \
           self.opcode == "FLOAT2INTS" or \
           self.opcode == "INT2FLOATS" or \
           self.opcode == "STRI2INTS":

            if self.args != 0:
                err.exit_script(err.lexical_or_syntax)            
            
        #1 arg: var
        elif self.opcode == "DEFVAR" or \
             self.opcode == "POPS":
            if self.args != 1 or \
                not self.arg1.is_valid_var():
                err.exit_script(err.lexical_or_syntax)            

        #1 arg: label
        elif self.opcode == "LABEL" or \
           self.opcode == "JUMP" or \
           self.opcode == "CALL" or \
           self.opcode == "JUMPIFEQS" or \
           self.opcode == "JUMPIFNEQS":
            if self.args != 1 or \
                not self.arg1.is_valid_label():
                err.exit_script(err.lexical_or_syntax)            

        #1 arg: symb
        elif self.opcode == "PUSHS" or \
           self.opcode == "WRITE" or \
           self.opcode == "EXIT" or \
           self.opcode == "DPRINT":
            if self.args != 1 or \
                not self.arg1.is_valid_symb():
                err.exit_script(err.lexical_or_syntax)            

        #2 arg: var symb
        elif self.opcode == "MOVE" or \
           self.opcode == "INT2CHAR" or \
           self.opcode == "INT2FLOAT" or \
           self.opcode == "FLOAT2INT" or \
           self.opcode == "STRLEN" or \
           self.opcode == "TYPE" or \
           self.opcode == "NOT":
            if self.args != 2 or \
                not self.arg1.is_valid_var() or \
                not self.arg2.is_valid_symb():
                err.exit_script(err.lexical_or_syntax)            

        #2 arg: var type
        elif self.opcode == "READ":
            if self.args != 2 or \
                not self.arg1.is_valid_var() or \
                not self.arg2.is_valid_type():
                err.exit_script(err.lexical_or_syntax)            

        #3 arg: var symb symb
        elif self.opcode == "ADD" or \
           self.opcode == "SUB" or \
           self.opcode == "MUL" or \
           self.opcode == "IDIV" or \
           self.opcode == "DIV" or \
           self.opcode == "LT" or \
           self.opcode == "GT" or \
           self.opcode == "EQ" or \
           self.opcode == "AND" or \
           self.opcode == "OR" or \
           self.opcode == "STRI2INT" or \
           self.opcode == "CONCAT" or \
           self.opcode == "GETCHAR" or \
           self.opcode == "SETCHAR":
            if self.args != 3 or \
                not self.arg1.is_valid_var() or \
                not self.arg2.is_valid_symb() or \
                not self.arg3.is_valid_symb():
                err.exit_script(err.lexical_or_syntax)            
            

        #3 arg: label symb symb
        elif self.opcode == "JUMPIFEQ" or \
           self.opcode == "JUMPIFNEQ":
            if self.args != 3 or \
                not self.arg1.is_valid_label() or \
                not self.arg2.is_valid_symb() or \
                not self.arg3.is_valid_symb():
                err.exit_script(err.lexical_or_syntax)            

        else:
            err.exit_script(err.lexical_or_syntax)


    def print(self):
        """ Prints current instruction for debugging purposes """

        if self.args == 0:
            print("= Instruction: [", self.opcode, "]", sep='', end='')
        elif self.args == 1:
            print("= Instruction: [", self.opcode, "]\t[", self.arg1.datatype, " : ", self.arg1.frame, " : ", self.arg1.value, "]", sep='', end='')
        elif self.args == 2:
            print("= Instruction: [", self.opcode, "]\t[", self.arg1.datatype, " : ", self.arg1.frame, " : ", self.arg1.value, "]\t[", self.arg2.datatype, " : ", self.arg2.frame, " : ", self.arg2.value, "]", sep='', end='')
        elif self.args == 3:
            print("= Instruction: [", self.opcode, "]\t[", self.arg1.datatype, " : ", self.arg1.frame, " : ", self.arg1.value, "]\t[", self.arg2.datatype, " : ", self.arg2.frame, " : ", self.arg2.value, "]\t[", self.arg3.datatype, " : ", self.arg3.frame, " : ", self.arg3.value, "]", sep='', end='')

    def debug(self):
        """ Interpretes instructions step by step for debugging purposes """

        self.print()
        input()
