#!/usr/bin/env python3

import sys
from xml.dom import minidom
from symtable import SymTable
from instruction import Instruction
from arg import Arg
from labels import Labels
from error import *
import argparse
 
def print_stats_to_file(file, cnt_insts, cnt_vars):
    """ Used by STATI extension, writes statistics to an output file """

    for arg in sys.argv:
        if arg == "--insts":
            file.write(str(cnt_insts) + "\n")
        elif arg == "--vars":
            file.write(str(cnt_vars) + "\n")


### Argument parsing ###
if ("--help" in sys.argv or "-h" in sys.argv) and len(sys.argv) > 2:
    err.exit_script(err.missing_parameter)

parser = argparse.ArgumentParser()
parser.add_argument("--source", dest="source_file", help="input xml file, stdin will be used by default if not set")
parser.add_argument("--input", dest="input_file", help="input for source code interpretation, stdin will be used by default if not set (either --source or --input parameter must be set)")
parser.add_argument("--stats", dest="stats_file", help="output file for some interpretation statistics")
parser.add_argument("--insts", dest="stats_insts", help="prints amount of interpreted instructions into file set by --stats parameter", action="store_true")
parser.add_argument("--vars", dest="stats_vars", help="prints amount of defined variables into file set by --stats parameter", action="store_true")
parser.add_argument("--debug", dest="debug_mode", help="runs the interpreter in debug mode", action="store_true")
args = parser.parse_args()

# Both source file and input file not set
if (args.source_file == None and args.input_file == None):
    err.exit_script(err.missing_parameter)

# Read instructions from source file or stdin
if (args.source_file != None):
    source_file_stream = args.source_file
else:
    source_file_stream = sys.stdin

# Check whether source XML is well-formed
try:
    xml = minidom.parse(source_file_stream)
except:
    err.exit_script(err.xml)

# Read input from stdin or redirect input file to stdin
if (args.input_file != None):
    old_stdin = sys.stdin
    try:
        sys.stdin = open(args.input_file)
    except:
        err.exit_script(err.output_file)

# Check for STATI extension parameters
if (args.stats_insts or args.stats_vars):
    if (args.stats_file != None):
        try:
            stats_file_stream = open(args.stats_file, "w")
        except:
            err.exit_script(err.output_file)
    else:
        err.exit_script(err.missing_parameter)

# Custom debug mode
debug = False
if (args.debug_mode):
    debug = True

### Reading XML source file ###
# Check for language="IPPcode19"
if "language" not in xml.firstChild.attributes:
    err.exit_script(err.lexical_or_syntax)
if xml.firstChild.attributes["language"].value != "IPPcode19":
    err.exit_script(err.lexical_or_syntax)

# Check for excessive text in XML
for node in xml.firstChild.childNodes:
    if node.nodeType == node.TEXT_NODE:
        if (not node.nodeValue.isspace()):
            err.exit_script(err.lexical_or_syntax)
    elif node.nodeType == node.ELEMENT_NODE:
        if node.localName != "instruction":
            err.exit_script(err.lexical_or_syntax)

# Check for order attribute in instruction elements
instructions = xml.getElementsByTagName("instruction")
for err.inst_order in range (0, len(instructions)):
    if "order" not in instructions[err.inst_order].attributes:
        err.exit_script(err.lexical_or_syntax)

# Sort instruction elements by order number
instructions.sort(key=lambda x: int(x.attributes["order"].value))

# Check for valid order sequence
order_check = 1
for inst in instructions:
    if order_check != int(inst.attributes["order"].value):
        err.exit_script(err.lexical_or_syntax)
    order_check += 1

### Interpretation ###
# 1st passing of all instructions to define labels
labels = Labels()
err.inst_order = 0
for inst_order in range (0, len(instructions)):
    err.inst_order += 1
    inst = Instruction(instructions[inst_order])
    if inst.opcode == "LABEL":
        labels.add(inst.arg1, inst_order)

# 2nd passing of all instructions to interprete them
inst_order = 0
inst_exectuted = 0
err.inst_order = 0
symtable = SymTable()

while inst_order < len(instructions):
    err.inst_order += 1
    inst = Instruction(instructions[inst_order])
    
    if debug == True:
        inst.debug()

    if   inst.opcode == "CREATEFRAME":
        symtable.create_frame()
    elif inst.opcode == "PUSHFRAME":
        symtable.push_frame()
    elif inst.opcode == "POPFRAME":
        symtable.pop_frame()
    elif inst.opcode == "RETURN":
        inst_order = labels.ret()
    elif inst.opcode == "BREAK":
        sys.stderr.write("Instructions order: " + str(inst_order + 1) + "\n")
        sys.stderr.write("Instructions executed: " + str(inst_exectuted + 1) + "\n")
        symtable.print()
    elif inst.opcode == "CLEARS":
        symtable.clears()

    #1 arg: var
    elif inst.opcode == "DEFVAR":
        symtable.defvar(inst.arg1)
    elif inst.opcode == "POPS":
        symtable.set_var(inst.arg1, symtable.pops())

    #1 arg: label
    elif inst.opcode == "JUMP":
        inst_order = labels.jump(inst.arg1)

    elif inst.opcode == "CALL":
        inst_order = labels.call(inst.arg1, inst_order)

    #1 arg: symb
    elif inst.opcode == "PUSHS":
        symtable.pushs(inst.arg1)
    elif inst.opcode == "WRITE":
        symtable.get_value(inst.arg1).write(sys.stdout)

    elif inst.opcode == "EXIT":
        exit_arg = symtable.get_value(inst.arg1)
        
        if exit_arg.datatype == "int":
            if  0 <= exit_arg.value <= 49:
                if args.stats_file != None:
                    print_stats_to_file(stats_file_stream, inst_exectuted, symtable.max_defined_vars)
                sys.exit(exit_arg.value)
            else:
                err.exit_script(err.operand_value)
        else:
            err.exit_script(err.operand_type)
        
    elif inst.opcode == "DPRINT":
        symtable.get_value(inst.arg1).write(sys.stderr)

    #2 arg: var symb
    elif inst.opcode == "MOVE":
        move_arg = symtable.get_value(inst.arg2)
        symtable.set_var(inst.arg1, move_arg)

    elif inst.opcode == "INT2CHAR" or inst.opcode == "INT2CHARS":
        if inst.opcode == "INT2CHAR":
            operand1_arg = symtable.get_value(inst.arg2)
        else:
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "string"

        if operand1_arg.datatype == "int":
            if 0 <= operand1_arg.value <= 1114111:
                result_arg.value = chr(operand1_arg.value)
            else:
                err.exit_script(err.string_operation)
        else:
            err.exit_script(err.operand_type)
        
        if inst.opcode == "INT2CHAR":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "STRLEN":
        operand1_arg = symtable.get_value(inst.arg2)
        result_arg = Arg(None)
        result_arg.datatype = "int"

        if operand1_arg.datatype == "string":
            result_arg.value = len(operand1_arg.value)
        else:
            err.exit_script(err.operand_type)
        symtable.set_var(inst.arg1, result_arg)

    elif inst.opcode == "TYPE":
        src_var = symtable.get_var_even_uninitialised(inst.arg2)
        dst_var = Arg(None)
        dst_var.datatype = "string"

        if src_var == None:
            dst_var.value = ""
        elif src_var.datatype == "int":
            dst_var.value = "int"
        elif src_var.datatype == "bool":
            dst_var.value = "bool"
        elif src_var.datatype == "string":
            dst_var.value = "string"
        elif src_var.datatype == "nil":
            dst_var.value = "nil"
        elif src_var.datatype == "float":
            dst_var.value = "float"
        
        symtable.set_var(inst.arg1, dst_var)

    #2 arg: var type
    elif inst.opcode == "READ":
        input_arg = Arg(None)
        input_arg.read(inst.arg2.value)
        symtable.set_var(inst.arg1, input_arg)

    #3 arg: var symb symb
    elif inst.opcode == "ADD" or inst.opcode == "ADDS":
        if inst.opcode == "ADD":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()

        result_arg = Arg(None)

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            result_arg.datatype = "int"
            result_arg.value = operand1_arg.value + operand2_arg.value
        elif operand1_arg.datatype == "float" and operand2_arg.datatype == "float":
            result_arg.datatype = "float"
            result_arg.value = operand1_arg.value + operand2_arg.value
        else:
            err.exit_script(err.operand_type)
        
        if inst.opcode == "ADD":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "SUB" or inst.opcode == "SUBS":
        if inst.opcode == "SUB":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            result_arg.datatype = "int"
            result_arg.value = operand1_arg.value - operand2_arg.value
        elif operand1_arg.datatype == "float" and operand2_arg.datatype == "float":
            result_arg.datatype = "float"
            result_arg.value = operand1_arg.value - operand2_arg.value
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "SUB":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "MUL" or inst.opcode == "MULS":
        if inst.opcode == "MUL":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            result_arg.datatype = "int"
            result_arg.value = operand1_arg.value * operand2_arg.value
        elif operand1_arg.datatype == "float" and operand2_arg.datatype == "float":
            result_arg.datatype = "float"
            result_arg.value = operand1_arg.value * operand2_arg.value
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "MUL":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "IDIV" or inst.opcode == "IDIVS":
        if inst.opcode == "IDIV":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "int"

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            if operand2_arg.value == 0:
                err.exit_script(err.operand_value)
            else:
                result_arg.value = operand1_arg.value // operand2_arg.value
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "IDIV":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "DIV" or inst.opcode == "DIVS":
        if inst.opcode == "DIV":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "float"

        if operand1_arg.datatype == "float" and operand2_arg.datatype == "float":
            if operand2_arg.value == 0:
                err.exit_script(err.operand_value)
            else:
                result_arg.value = operand1_arg.value / operand2_arg.value
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "DIV":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "LT" or inst.opcode == "LTS":
        if inst.opcode == "LT":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "bool"
        result_arg.value = "false"

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            if operand1_arg.value < operand2_arg.value:
                result_arg.value = "true"
        elif operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool":
            if operand1_arg.value == "false" and operand2_arg.value == "true":
                result_arg.value = "true"
        elif operand1_arg.datatype == "string" and operand2_arg.datatype == "string":
            if operand1_arg.value < operand2_arg.value:
                result_arg.value = "true"
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "LT":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "GT" or inst.opcode == "GTS":
        if inst.opcode == "GT":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "bool"
        result_arg.value = "false"

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            if operand1_arg.value > operand2_arg.value:
                result_arg.value = "true"

        elif operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool":
            if operand1_arg.value == "true" and operand2_arg.value == "false":
                result_arg.value = "true"

        elif operand1_arg.datatype == "string" and operand2_arg.datatype == "string":
            if operand1_arg.value > operand2_arg.value:
                result_arg.value = "true"

        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "GT":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "EQ" or inst.opcode == "EQS":
        if inst.opcode == "EQ":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "bool"
        result_arg.value = "false"

        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int":
            if operand1_arg.value == operand2_arg.value:
                result_arg.value = "true"
        elif operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool":
            if operand1_arg.value == operand2_arg.value:
                result_arg.value = "true"
        elif operand1_arg.datatype == "string" and operand2_arg.datatype == "string":
            if operand1_arg.value == operand2_arg.value:
                result_arg.value = "true"
        elif operand1_arg.datatype == "nil" and operand2_arg.datatype == "nil":
            if operand1_arg.value == operand2_arg.value:
                result_arg.value = "true"
        elif operand1_arg.datatype == "nil" or operand2_arg.datatype == "nil":
            ...
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "EQ":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "AND" or inst.opcode == "ANDS":
        if inst.opcode == "AND":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "bool"

        if operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool":
            if operand1_arg.value == "true" and operand2_arg.value == "true":
                result_arg.value = "true"
            else:
                result_arg.value = "false"
        else:
            err.exit_script(err.operand_type)

        if inst.opcode == "AND":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "OR" or inst.opcode == "ORS":
        if inst.opcode == "OR":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "bool"

        if operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool":
            if operand1_arg.value == "true" or operand2_arg.value == "true":
                result_arg.value = "true"
            else:
                result_arg.value = "false"
        else:
            err.exit_script(err.operand_type)  

        if inst.opcode == "OR":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "NOT" or inst.opcode == "NOTS":
        if inst.opcode == "NOT":
            operand1_arg = symtable.get_value(inst.arg2)
        else:
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "bool"

        if operand1_arg.datatype == "bool":
            if operand1_arg.value == "true":
                result_arg.value = "false"
            else:
                result_arg.value = "true"
        else:
            err.exit_script(err.operand_type)       

        if inst.opcode == "NOT":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "STRI2INT" or inst.opcode == "STRI2INTS":
        if inst.opcode == "STRI2INT":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "int"

        if operand1_arg.datatype == "string" and operand2_arg.datatype == "int":
            if 0 <= operand2_arg.value < len(operand1_arg.value):
                result_arg.value = ord(operand1_arg.value[operand2_arg.value])
            else:
                err.exit_script(err.string_operation)
        else:
            err.exit_script(err.operand_type)
        if inst.opcode == "STRI2INT":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "FLOAT2INT" or inst.opcode == "FLOAT2INTS":
        if inst.opcode == "FLOAT2INT":
            operand1_arg = symtable.get_value(inst.arg2)
        else:
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "int"

        if operand1_arg.datatype == "float":
            result_arg.value = int(operand1_arg.value)
        else:
            err.exit_script(err.operand_type)
        if inst.opcode == "FLOAT2INT":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "INT2FLOAT" or inst.opcode == "INT2FLOATS":
        if inst.opcode == "INT2FLOAT":
            operand1_arg = symtable.get_value(inst.arg2)
        else:
            operand1_arg = symtable.pops()
        result_arg = Arg(None)
        result_arg.datatype = "float"

        if operand1_arg.datatype == "int":
            result_arg.value = float(operand1_arg.value)
        else:
            err.exit_script(err.operand_type)
        if inst.opcode == "INT2FLOAT":
            symtable.set_var(inst.arg1, result_arg)
        else:
            symtable.pushs(result_arg)

    elif inst.opcode == "CONCAT":
        operand1_arg = symtable.get_value(inst.arg2)
        operand2_arg = symtable.get_value(inst.arg3)
        
        if operand1_arg.datatype == "string" and operand2_arg.datatype == "string":
            result_arg = Arg(None)
            result_arg.datatype = "string"
            result_arg.value = operand1_arg.value + operand2_arg.value
            symtable.set_var(inst.arg1, result_arg)
        else:
            err.exit_script(err.operand_type)
        symtable.set_var(inst.arg1, result_arg)

    elif inst.opcode == "GETCHAR":
        operand1_arg = symtable.get_value(inst.arg2)
        operand2_arg = symtable.get_value(inst.arg3)
        result_arg = Arg(None)
        result_arg.datatype = "int"

        if operand1_arg.datatype == "string" and operand2_arg.datatype == "int":
            if 0 <= operand2_arg.value < len(operand1_arg.value):
                result_arg.value = operand1_arg.value[operand2_arg.value]
            else:
                err.exit_script(err.string_operation)
        else:
            err.exit_script(err.operand_type)
        symtable.set_var(inst.arg1, result_arg)

    elif inst.opcode == "SETCHAR":
        operand1_arg = symtable.get_value(inst.arg2)
        operand2_arg = symtable.get_value(inst.arg3)
        result_arg = symtable.get_var(inst.arg1)

        if result_arg.datatype == "string" and operand1_arg.datatype == "int" and operand2_arg.datatype == "string":
            if 0 <= operand1_arg.value < len(result_arg.value) and len(operand2_arg.value) > 0:
                result_string = list(result_arg.value)
                result_string[operand1_arg.value] = operand2_arg.value[0]
                result_arg.value = "".join(result_string)
            else:
                err.exit_script(err.string_operation)
        else:
            err.exit_script(err.operand_type)
        symtable.set_var(inst.arg1, result_arg)

    #3 arg: label symb symb
    elif inst.opcode == "JUMPIFEQ" or inst.opcode == "JUMPIFEQS":
        if inst.opcode == "JUMPIFEQ":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand2_arg = symtable.pops()
            operand1_arg = symtable.pops()
        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int" or \
            operand1_arg.datatype == "string" and operand2_arg.datatype == "string" or \
            operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool" or \
            operand1_arg.datatype == "nil" and operand2_arg.datatype == "nil":
            if operand1_arg.value == operand2_arg.value:
                inst_order = labels.jump(inst.arg1)
        else:
            err.exit_script(err.operand_type)
        
    elif inst.opcode == "JUMPIFNEQ" or inst.opcode == "JUMPIFNEQS":
        if inst.opcode == "JUMPIFNEQ":
            operand1_arg = symtable.get_value(inst.arg2)
            operand2_arg = symtable.get_value(inst.arg3)
        else:
            operand1_arg = symtable.pops()
            operand2_arg = symtable.pops()
        if operand1_arg.datatype == "int" and operand2_arg.datatype == "int" or \
            operand1_arg.datatype == "string" and operand2_arg.datatype == "string" or \
            operand1_arg.datatype == "bool" and operand2_arg.datatype == "bool" or \
            operand1_arg.datatype == "nil" and operand2_arg.datatype == "nil":
            if operand1_arg.value != operand2_arg.value:
                inst_order = labels.jump(inst.arg1)
        else:
            err.exit_script(err.operand_type)

    inst_order += 1
    inst_exectuted += 1

    if args.stats_vars:
        symtable.count_vars()

if args.stats_file != None:
    print_stats_to_file(stats_file_stream, inst_exectuted, symtable.max_defined_vars)            
