from error import *

class SymTable:
    glob = dict()
    temp = None
    temp_defined = False
    local_stack = []
    local_defined = False
    var_stack = []
    max_defined_vars = 0

    def __is_frame_defined__(self, arg):
        """ Returns whether variable's frame is defined """

        if arg.frame == "GF":
            return True
        elif arg.frame == "TF" and self.temp_defined == True:
            return True
        elif arg.frame == "LF" and self.local_defined == True:
            return True
        else:
            return False
    
    def __is_var_defined__(self, arg):
        """ Returns whether a variable is defined """

        if arg.frame == "GF" and arg.value in self.glob:
            return True
        elif arg.frame == "TF" and arg.value in self.temp:
            return True
        elif arg.frame == "LF" and arg.value in self.local_stack[-1]:
            return True
        else:
            return False
        
    def create_frame(self):
        """ Creates an empty temporary frame """

        if self.temp_defined == False:
            self.temp = dict()
            self.temp_defined = True
        else:
            self.temp.clear()

    def push_frame(self):
        """ Pushes a temporary frame to the local frame stack """

        if self.temp_defined == False:
            err.exit_script(err.undef_frame)
        else:
            self.local_stack.append(self.temp)
            self.local_defined = True
            self.temp = None
            self.temp_defined = False
    
    def pop_frame(self):
        """ Pops a frame from the local frame stack """

        if len(self.local_stack) == 0:
            err.exit_script(err.undef_frame)
        else:
            self.temp = self.local_stack.pop()
            self.temp_defined = True
            if len(self.local_stack) == 0:
                self.local_defined = False

    def defvar(self, arg):
        """ Defines a variable """

        if self.__is_frame_defined__(arg) == False:
            err.exit_script(err.undef_frame)
        if self.__is_var_defined__(arg) == True:
            err.exit_script(err.semantics)  # Undefined variable

        if arg.frame == "GF":
            self.glob[arg.value] = None
        elif arg.frame == "TF":
            self.temp[arg.value] = None
        elif arg.frame == "LF":
            self.local_stack[-1][arg.value] = None
    
    def set_var(self, arg1, arg2):
        """ Assigns a value to a variable """

        if self.__is_frame_defined__(arg1) == False:
            err.exit_script(err.undef_frame)
        if self.__is_var_defined__(arg1) == False:
            err.exit_script(err.undef_var)

        if arg1.frame == "GF":
            self.glob[arg1.value] = arg2
        elif arg1.frame == "TF":
            self.temp[arg1.value] = arg2
        elif arg1.frame == "LF":
            self.local_stack[-1][arg1.value] = arg2


    def get_var (self, arg):
        """ Gets a value from a variable """

        if self.__is_frame_defined__(arg) == False:
            err.exit_script(err.undef_frame)
        if self.__is_var_defined__(arg) == False:
            err.exit_script(err.undef_var)

        if arg.frame == "GF":
            arg_get = self.glob[arg.value]
        elif arg.frame == "TF":
            arg_get = self.temp[arg.value]
        elif arg.frame == "LF":
            arg_get = self.local_stack[-1][arg.value]
        
        if arg_get == None:
            err.exit_script(err.missing_value)
        return arg_get

    def get_var_even_uninitialised(self, arg):
        """ Gets a value from a variable, doesn't check whether the variable is initialised """

        if self.__is_frame_defined__(arg) == False:
            err.exit_script(err.undef_frame)
        if self.__is_var_defined__(arg) == False:
            err.exit_script(err.undef_var)

        if arg.frame == "GF":
            arg_get = self.glob[arg.value]
        elif arg.frame == "TF":
            arg_get = self.temp[arg.value]
        elif arg.frame == "LF":
            arg_get = self.local_stack[-1][arg.value]
        return arg_get

    def get_value(self, arg):
        """ Returns a constant or gets a value from a variable """

        if arg.datatype == "var":
            return self.get_var(arg)
        else:
            return arg

    def print(self):
        """ Prints frame contents """

        sys.stderr.write("Frame contents:\n")
        sys.stderr.write("Global frame:\n")
        for var in self.glob:
            if self.glob[var] == None:
                sys.stderr.write("\tVar: " + var + ",\tUndefined value\n")
            else:
                sys.stderr.write("\tVar: " + var + ",\ttype: " + self.glob[var].datatype + ",\tvalue: " + str(self.glob[var].value) + "\n")
        sys.stderr.write("Temporary frame: defined: " + str(self.temp_defined) + "\n")

        if self.temp_defined:
            for var in self.temp:
                if self.temp[var] == None:
                    sys.stderr.write("\tVar: " + var + ",\tUndefined value\n")
                else:
                    sys.stderr.write("\tVar: " + var + ",\ttype: " + self.temp[var].datatype + ",\tvalue: " + str(self.temp[var].value) + "\n")
        sys.stderr.write("Local frame: defined: " + str(self.local_defined) + "\n")

        if self.local_defined:
            frame_cntr = 0
            for frame in self.local_stack:
                sys.stderr.write("\tFrame " + str(frame_cntr) + ":\n")
                frame_cntr += 1
                for var in frame:
                    if frame[var] == None:
                        sys.stderr.write("\t\tVar: " + var + ",\tUndefined value\n")
                    else:
                        sys.stderr.write("\t\tVar: " + var + ",\ttype: " + frame[var].datatype + ",\tvalue: " + frame[var].value + "\n")
        
    def pushs(self, arg):
        """ Pushes a value to the value stack """

        self.var_stack.append(self.get_value(arg))

    def pops(self):
        """ Pops a value from the value stack """

        if len(self.var_stack) == 0:
            err.exit_script(err.missing_value)
        else:
            return self.var_stack.pop()
    
    def clears(self):
        """ Clears the value stack """

        self.var_stack.clear()
    
    def count_vars(self):
        """ Counts initialised variables in all frames and sets the maximum value """

        counter = 0

        for var, value in self.glob.items():
            print(var,value)
            if value != None:
                counter += 1
        
        if self.temp_defined:
            for var, value in self.temp.items():
                if value != None:
                    counter += 1

        if self.local_defined:
            for frame in self.local_stack:
                for var, value in frame.items():
                    if value != None:
                        counter += 1

        if counter > self.max_defined_vars:
            self.max_defined_vars = counter
