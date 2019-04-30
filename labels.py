from error import *

class Labels:
    labels = dict()
    call_stack = []

    def jump(self, arg):
        """ Jumps to a label (returns order of a label) """

        if arg.value in self.labels:
            return self.labels[arg.value]
        else:
            err.exit_script(err.semantics)
    
    def add(self, arg, inst_order):
        """ Adds a new label to a dictionary of labels """

        if arg.value in self.labels:
            err.exit_script(err.semantics)
        self.labels[arg.value] = inst_order
    
    def call(self, arg, inst_order):
        """ Adds current position to a call stack and jumps to a label """

        self.call_stack.append(inst_order)
        return self.jump(arg)
    
    def ret(self):
        """ Pops a value from call stack """

        if len(self.call_stack) == 0:
            err.exit_script(err.missing_value)
        else:
            return self.call_stack.pop()
    
    def print(self):
        """ Prints defined labels and call stack for debugging purposes """
    
        print("Labels:")
        print("=", self.labels)
        print("Call stack:")
        print("=", self.call_stack)

