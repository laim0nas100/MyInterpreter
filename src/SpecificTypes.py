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


class TFunction(TVariable):
    def __init__(self, t: list, name, parameters: list):
        super().__init__(t, name)
        self.parameters = []
        for p in parameters:
            self.parameters.append(p.tp)



class Reg:
    def __init__(self,name):
        self.name = name
        self.t = None
        self.value = None

    def __str__(self):
        return self.name +" "+ str(self.t) +" "+ str(self.value)

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

    def modify(self,index:Reg,val:Reg):
        if not index.t == LexName.INT:
            if not index.value < self.size:
                if not val.t == self.t:
                    self.set(index.value, val.value)
                else:
                    raise SemanticException("Array type miss match")
            else:
                raise SemanticException("Array Out of bounds")
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
        self.index = 0

    def getExitLabel(self):
        return "E"+self.label

    def getParentLabel(self):
        indexOfB = str.index(self.label, "B")
        return self.label[1 + indexOfB:]

    def getBlockInfo(self):
        string = "Block ["+self.label+"]\n"
        string += "functions:"
        for f in self.functions.values():
            string+= "\n"+f.t.__str__() + " def "+f.name+" "
            for p in f.parameters:
                string+=p.__str__()+" "
        string+="\nvars:"
        for var in self.variables.values():
            string+= "\n"+str(var)
        string+="\n### END ###"
        return string


class Operation:
    @staticmethod
    def copyValue(original: TVariable)->TVariable:
        var = TVariable([original.t, original.isArray], original.name)
        var.t = original.t()
        if isinstance(original.value, StaticArray):
            var.value = StaticArray(original.value.size,original.value.t)
            for i in range(0,original.value.size):
                var.value[i] = Operation.copyValue(original.value[i])
        else:
            var.value = original.value
        return var



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
        [LexName.BOOL, LexName.NULL]
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
        [LexName.BOOL, LexName.NULL]
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


