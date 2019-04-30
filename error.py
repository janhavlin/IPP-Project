import sys
import inspect

class Error:
    missing_parameter = 10
    input_file = 11
    output_file = 12
    xml = 31
    lexical_or_syntax = 32
    semantics = 52
    operand_type = 53
    undef_var = 54
    undef_frame = 55
    missing_value = 56
    operand_value = 57
    string_operation = 58
    runtime = 99
    inst_order = 0

    def exit_script(self, errcode):
        """ Exits the interpreter in case of an error and prints some information to stderr """
    
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        sys.stderr.write("Error called by method: " + calframe[1][3])

        frame_records = inspect.stack()
        calling_module = inspect.getmodulename(frame_records[1][1])
        sys.stderr.write(" in module: " + calling_module)
        
        sys.stderr.write(" on line: " + str(frame_records[1][2]) + "\n")

        if errcode == self.missing_parameter:
            sys.stderr.write("Error: Invalid input parameters\n")
        elif errcode == self.input_file:
            sys.stderr.write("Error: Invalid input file\n")
        elif errcode == self.output_file:
            sys.stderr.write("Error: Invalid output file\n")
        elif errcode == self.xml:
            sys.stderr.write("Error: XML not well-formed\n")
        elif errcode == self.lexical_or_syntax:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Lexical or syntax\n")
        elif errcode == self.semantics:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Semantic error of input code\n")
        elif errcode == self.operand_type:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Incompatible operand types\n")
        elif errcode == self.undef_var:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Using undefined variable\n")
        elif errcode == self.undef_frame:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Using undefined frame\n")
        elif errcode == self.missing_value:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Missing value\n")
        elif errcode == self.operand_value:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Invalid operand value\n")
        elif errcode == self.string_operation:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Invalid string operation\n")
        elif errcode == self.runtime:
            sys.stderr.write("Error at inst " + str(self.inst_order) + ": Runtime\n")
        else:
            sys.stderr.write("Error at inst " + str(self.inst_order) + "\n")
        exit(errcode)

err = Error()
