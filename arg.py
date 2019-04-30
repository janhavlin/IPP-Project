import re
from error import *

class Arg:
    datatype = None
    frame = None
    value = None

    def __init__(self, arg):
        """ Extracts values from <argN> XML element
        if the parameter is None it will define empty Argument """

        if arg == None:
            return
        if len(arg.attributes) != 1:
            err.exit_script(err.lexical_or_syntax)

        if "type" not in arg.attributes:
            err.exit_script(err.lexical_or_syntax)
        self.datatype = arg.attributes["type"].value
        
        if arg.firstChild == None and self.datatype != "string":
            err.exit_script(err.lexical_or_syntax)

        if self.datatype == "var":
            self.frame = arg.firstChild.nodeValue.partition("@")[0]
            self.value = arg.firstChild.nodeValue.partition("@")[2]
        else:
            self.frame = None
            if arg.firstChild != None:
                self.value = arg.firstChild.nodeValue
                if self.datatype == "string":
                    self.value = self.decode_string()
            else:
                self.value = ""

    def write(self, std):
        """ Writes its own value to a specified output stream """

        if self.datatype == "nil":
            std.write("")
        elif self.datatype == "float":
            std.write(self.value.hex())
        else:
            std.write(str(self.value))

    def read(self, datatype):
        """ Reads a value from stdin with type specified by datatype """

        try:
            self.datatype = datatype
            input_value = input()
        except:
            if datatype == "int":
                self.value = 0
            elif datatype == "bool":
                self.value = "false"
            elif datatype == "string":
                self.value = ""
            elif datatype == "float":
                self.value = 0.0
            return

        if datatype == "int":
            self.value = input_value
            if not self.is_valid_int():
                self.value = 0
        elif datatype == "bool": 
            if input_value.upper() == "TRUE":
                self.value = "true"
            else:
                self.value = "false"
        elif datatype == "string": 
            self.value = input_value
            #if not self.is_valid_string():     # Lexical check shouldn't be needed...
            #    self.value = ""
        elif datatype == "float": 
            self.value = input_value
            if not self.is_valid_float():
                self.value = 0.0

    def decode_string(self):
        """ Converts string's escape sequences into regular characters """

        def replace(match):
            return chr(int(match.group()[1:]))

        regex = re.compile(r"\\[0-9][0-9][0-9]")
        return re.sub(regex, replace, self.value)

    def is_valid_int(self):
        """ Lexically checks whether the value is a valid integer and converts it """

        if self.datatype == "int":
            if self.value.isdigit() or  \
            self.value[0] == "+" and self.value[1:].isdigit() or    \
            self.value[0] == "-" and self.value[1:].isdigit():
                self.value = int(self.value)
                return True
        return False
    
    def is_valid_bool(self):
        """ Lexically checks whether the value is a valid bool """

        if self.datatype == "bool" and (self.value == "true" or self.value == "false"):
            return True
        return False
    
    def is_valid_string(self):
        """ Lexically checks whether the value is a valid string """

        if self.datatype == "string":
            pattern = re.compile(r"^([^#\\\\]|(\\\\[0-9][0-9][0-9]))*$")
            result = re.match(pattern, self.value)
            if result != None:
                return True
        return False
    
    def is_valid_float(self):
        """ Converts hexadecimal float into regular float """

        if self.datatype == "float":
            self.value = float.fromhex(self.value)
            return True
        return False

    def is_valid_var(self):
        """ Lexically checks whether the value is a valid variable name """

        if self.datatype == "var" and self.frame == "GF" or self.frame == "TF" or self.frame == "LF":
            pattern = re.compile(r"^[a-zA-Z_$&%*!?\-][a-zA-Z0-9_$&%*!?\-]*$")
            result = re.match(pattern, self.value)
            if result != None:
                return True
        return False

    def is_valid_symb(self):
        """ Lexically checks whether the value is a valid symb """

        if self.is_valid_var() or self.is_valid_int() or self.is_valid_bool() or self.is_valid_string() or self.is_valid_float():
            return True
        elif self.datatype == "nil" and self.value == "nil":
            return True
        return False
    
    def is_valid_label(self):
        """ Lexically checks whether the value is a valid label name """

        if self.datatype == "label":
            pattern = re.compile(r"^[a-zA-Z_$&%*!?\-][a-zA-Z0-9_$&%*!?\-]*$")
            result = re.match(pattern, self.value)
            if result != None:
                return True
        return False

    def is_valid_type(self):
        """ Lexically checks whether the value is a valid type """

        if self.datatype == "type":
            if self.value == "int" or self.value == "bool" or self.value == "string" or self.value == "float":
                return True
        return False
