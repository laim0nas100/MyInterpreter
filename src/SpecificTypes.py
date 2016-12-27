from definitions import SemanticException
from src.ASTnodes import Null
from src.LexNames import LexName
from src.lib import ArrayList, OrderedMap
import math

class TVariable:
    def __init__(self, t: list, name):
        self.t = t[0]
        self.isArray = t[1]
        self.name = name
        self.value = None

    def tp(self):
        string = str(self.t)
        if self.isArray:
            string += "[]"
        return string

    def __str__(self):
        string = self.t.__str__()
        if self.isArray:
            string += "[]"
        string += " " + self.name + "=" + str(self.value)
        return string

    def booleanValue(self):
        if isinstance(self.value,bool):
            return self.value
        if self.value is None:
            return False
        if isinstance(self.value,int):
            return not(self.value == 0)
        if input(self.value,float):
            if math.ceil(self.value) == math.floor(self.value):
                return not (math.ceil(self.value) == 0)
        return True

class TFunction():
    def __init__(self, t: list, name,label, parameters: list,function = None):
        self.t = t[0]
        self.isArray = t[1]
        self.name = name
        self.label = label
        self.execute = function
        # add a function object to execute at run-time that should return a value at the end
        # that will be pushed to a stack
        # must accept a list
        self.parameters = []
        for p in parameters:
            self.parameters.append(p.tp)

    def tp(self):
        string = str(self.t)
        if self.isArray:
            string += "[]"
        return string

class Reg:
    def __init__(self,name):
        self.name = name
        self.t = None
        self.value = None

    def __str__(self):
        return self.name +"["+ str(self.t)+","+str(self.value)+"];"

    def toTVariable(self):
        isArray = isinstance(self.value,list)
        var = TVariable([self.t,isArray],"_NullName")
        var.value = self.value
        return var

    def booleanValue(self):
        return self.toTVariable().booleanValue()

    def tp(self):
        string = str(self.t)
        if isinstance(self.value,list):
            string += "[]"
        return string

class StaticArray(ArrayList):
    def __init__(self,size:int,t:str):
        super().__init__(None,None)
        self.size = size
        self.t = t
        self.appendToSize(size)
        for i in range(0,size):
            self.set(i,TVariable([t,False],str(i)))

    def get(self,index:Reg):
        if index.tp() == LexName.INT:
            if index.value < self.size:
                return self[index.value]
            else:
                raise SemanticException("Array Access Out of bounds")
        else:
            raise SemanticException("Array index is not INT")

    def __str__(self):
        string = "["
        for v in self:
            string+=v.__str__() +","
        string = string[0:-1] + "]"
        return string

class Scope:
    def __init__(self,label):
        self.label = label
        self.statements = ArrayList(None,None)
        self.variables = OrderedMap()
        self.functions = OrderedMap()
        self.functionName = None
        self.returnIndex = 0
        self.registers = OrderedMap()

    def getExitLabel(self):
        return "E"+self.label

    def getParentLabel(self):
        indexOfB = str.index(self.label, "B")
        return self.label[1 + indexOfB:]

    def getBlockInfo(self):
        string = "Block ["+self.label+"]"
        if self.functionName:
            string+=self.functionName
        string+="\n"
        string += "functions:"
        for f in self.functions.values():
            string+= "\n"+f.t.__str__() + " "+f.name+" "+f.label+" "
            for p in f.parameters:
                string+=p.__str__()+" "
        string+="\nvars:"
        for var in self.variables.values():
            string+= "\n"+str(var)
        string+="\n### END ###"
        return string

    def __str__(self):
        return self.label

class Tnames:
    LOAD = "LOAD" #loads to register following value
    JUMP = "JUMP" #jumps within all scopes
    JUMPZ = "JUMPZ" #jump if operand is zero to label {x, label}
   # JUMPBLOCK = "JUMPBLOCK" #jump within scope
    LOADARR = "LOADARR" #loads to register x from [array, index]
    LABEL = "LABEL" #creates new label
    INIT = "INIT" #initialises new variable {type,value,name}
    INITARR = "INITARR" #initialises new array {size, [type,name]}
    CALLBLOCK = "CALLBLOCK" #jumps to block
    POP = "POP" #pops to register following value
    PUSH = "PUSH" #pushes to register the following value
    RETURN = "RETURN"
    ENDBLOCK = "ENDBLOCK" #does nothing, marks end of a block
    CALL = "CALL" #call a function

class TAC:
    def __init__(self,operation,operand0,operand1=None):
        if operand1 is None:
            self.tuple = [operation, operand0]
        else:
            self.tuple = [operation,operand0,operand1]
        self.operation = operation

    def __str__(self):
        s = ""
        for t in self.tuple:
            s += " "+t.__str__()
        return s+";"

    def __copy__(self):
        l = self.tuple.__len__()
        if l == 3:
            newTAC = TAC(self.operation,"","")
        else:
            newTAC = TAC(self.operation, "", None)
        i = 0
        for t in self.tuple:
            if isinstance(t,list):
                newTAC.tuple[i] = t.copy()
            else:
                newTAC.tuple[i] = t
            i+=1
        return newTAC

class Operation:
    @staticmethod
    def copyValue(original: TVariable)->TVariable:
        var = TVariable([original.t, original.isArray], original.name)
        var.t = original.t
        if isinstance(original.value, StaticArray):
            var.value = StaticArray(original.value.size,original.value.t)
            for i in range(0,original.value.size):
                var.value[i] = Operation.copyValue(original.value[i])
        else:
            var.value = original.value
        return var

    @staticmethod
    def copyFunction(original: TFunction) ->TFunction:
        tf= TFunction([original.t,original.isArray],original.name,original.label,[])
        tf.parameters = original.parameters.copy()
        return tf

    @staticmethod
    def generateScope(self:Scope,appendToLabel = ""):
        newScope = Scope(self.label+appendToLabel)

        for func in self.functions.returnItemsInOrder():
            newScope.functions.put(func.name,Operation.copyFunction(func))
        for var in self.variables.returnItemsInOrder():
            newScope.variables.put(var.name,Operation.copyValue(var))
        for st in self.statements:
            s = st.__copy__()
            if s.tuple[0] == Tnames.LABEL:
                s.tuple[1]+=appendToLabel
            newScope.statements.append(s)
        newScope.functionName = self.functionName
        return newScope


    _plus =[
        [LexName.INT,LexName.INT],
        [LexName.FLOAT,LexName.FLOAT],
        [LexName.FLOAT,LexName.INT],
        [LexName.STRING,LexName.STRING]
    ]
    _arit = [
        [LexName.INT, LexName.INT],
        [LexName.FLOAT, LexName.FLOAT],
        [LexName.FLOAT, LexName.INT]
    ]
    _aritCompare = [
        [LexName.INT, LexName.INT],
        [LexName.FLOAT, LexName.FLOAT],
        [LexName.INT, LexName.FLOAT],
        [LexName.FLOAT, LexName.INT]
    ]
    _assign = [
        [LexName.INT, LexName.INT],
        [LexName.FLOAT, LexName.FLOAT],
        [LexName.FLOAT, LexName.INT],
        [LexName.STRING, LexName.STRING],
        [LexName.BOOL, LexName.BOOL],
        [LexName.INT, LexName.NULL],
        [LexName.FLOAT, LexName.NULL],
        [LexName.STRING, LexName.NULL],
        [LexName.BOOL, LexName.NULL],
        [LexName.INT + "[]", LexName.INT + "[]"],
        [LexName.FLOAT + "[]", LexName.FLOAT + "[]"],
        [LexName.STRING + "[]", LexName.STRING + "[]"],
        [LexName.BOOL + "[]", LexName.BOOL + "[]"],
        [LexName.INT + "[]", LexName.NULL],
        [LexName.FLOAT + "[]", LexName.NULL],
        [LexName.STRING + "[]", LexName.NULL],
        [LexName.BOOL + "[]", LexName.NULL]
    ]

    _equal = [
        [LexName.INT, LexName.INT],
        [LexName.FLOAT, LexName.FLOAT],
        [LexName.FLOAT, LexName.INT],
        [LexName.STRING, LexName.STRING],
        [LexName.BOOL, LexName.BOOL],
        [LexName.INT, LexName.NULL],
        [LexName.FLOAT, LexName.NULL],
        [LexName.STRING, LexName.NULL],
        [LexName.BOOL, LexName.NULL],
        [LexName.INT + "[]", LexName.NULL],
        [LexName.FLOAT + "[]", LexName.NULL],
        [LexName.STRING + "[]", LexName.NULL],
        [LexName.BOOL + "[]", LexName.NULL]
    ]
    _logic = [
        [LexName.BOOL, LexName.BOOL],
        [LexName.BOOL, LexName.INT],
        [LexName.BOOL, LexName.FLOAT],
        [LexName.BOOL, LexName.NULL],
        [LexName.BOOL, LexName.STRING]
    ]



    @staticmethod
    def operationDefined(opType,t1,t2):
        op = [t1,t2]
        if opType == LexName.PLUS:
            return op in Operation._plus
        elif opType in [LexName.MINUS,LexName.MULTIPLY,LexName.DIVIDE]:
            return op in Operation._arit
        elif opType in LexName.ArithMethicCompare:
            return op in Operation._aritCompare
        elif opType == LexName.ASSIGN:
            return op in Operation._assign
        elif opType in [LexName.EQUALS,LexName.NOTEQUAL]:
            return op in Operation._equal
        elif opType in LexName.LogicOperators:
            return op in Operation._logic
        elif opType in LexName.AdvancedAssign:
            if opType == LexName.ASSIGNPLUS:
                return op in Operation._plus
            else:
                return op in Operation._arit


        return False


