from src.LexNames import LexName
from src.lexer import Token
from src.lib import ArrayList


def wrapxml(string,end=False)-> str:
    s = "<"
    if end:
        s+="/"
    s+=str(string)+">"
    return s+"\n"

class AST:
    className = "AST"
    def __init__(self):
        self.isEmpty = False

    def isEmpty(self):
        return self.isEmpty

    def __str__(self):
        return ""

    def xml(self,ob=None) -> str:
        return AST.className

    def toxml(self,ob = None, end = False)->str:
        if ob is not None:
            return wrapxml(ob,end)
        else:
            return wrapxml(self.className, end)

class Block(AST):
    className = "Block"

    def __init__(self):
        super().__init__()
        self.statements = list()
        self.children = list()
        self.parents = list()
        self.label = ""
        self.number = 0;

    def exitLabel(self):
        return "E"+self.label

    def isEmpty(self):
        return self.statements.__len__() == 0

    def __str__(self):
        s = "{\n"
        for st in self.statements:
            s+=st.__str__()+";\n"
        return s+"}"

    def xml(self,ob=className) ->str:
        s = self.toxml(ob)
        s+= "Label " +str(self.label)+"\n"
        s+= "Number "+str(self.number)+"\n"
        s+= "Parents"+str(self.parents)+"\n"
        s+= "Children"+str(self.children)+"\n"
        for st in self.statements:
            s+= st.xml()
        s+= self.toxml(ob,True)
        return s

class Root(Block):
    className = "Root"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return "ROOT"+super().__str__()

    def xml(self,ob=className):
        return super().xml(ob)

class Type(AST):
    className = "Type"

    def __init__(self, tp:str, isArray=False):
        super().__init__()
        self.tp = tp
        self.isArray = isArray

    def __str__(self):
        s = str(self.tp)
        if self.isArray:
            s+="[]"
        return s

    def xml(self,ob=className):
        s = self.toxml(ob)
        s+= str(self.tp)
        if self.isArray:
            s+="[]"
        s+= "\n"+self.toxml(ob,True)
        return s

class VariableDeclaration(Type):
    className = "VariableDeclaration"

    def __init__(self, tp, name):
        super().__init__(tp)
        self.name = name

    def __str__(self):
        s = str(self.tp)
        if self.isArray:
            s += "[]"
        return s + " "+str(self.name)

    def xml(self,ob=className):
        s = self.toxml(ob)
        s+= super().xml()
        s+= "name ="+str(self.name)
        s+= self.toxml(ob,True)
        return s

class VariableInitialization(VariableDeclaration):
    className = "VariableInitialization"

    def __init__(self, tp, name, value=None):
        super().__init__(tp,name)
        self.value = value

    def __str__(self):
        s = str(self.tp)
        if self.isArray:
            s += "[]"
        return s + " "+str(self.name)+" = "+str(self.value)

    def xml(self,ob=className):
        s = self.toxml(ob)
        s+= super().xml()
        s+= "value="+str(self.value.xml())
        s += self.toxml(ob,True)
        return s

class ArrayDeclaration(VariableDeclaration):
    className = "ArrayDeclaration"

    def __init__(self, tp, name, size):
        super().__init__(tp, name)
        self.value = ArrayList(None,None)
        self.size = size

    def xml(self,ob=className):
        s = self.toxml(ob)
        s+= super().xml()
        s+= "size="+self.size.xml()+"\n"

        s += self.toxml(ob,True)
        return s

class FunctionDeclaration(VariableDeclaration):
    className = "FunctionDeclaration"

    def __init__(self, tp, name, parameters:list,body):
        super().__init__(tp, name)
        self.parameters = parameters
        self.body = body

    def __str__(self):
        s = super().__str__()
        s+="("
        for p in self.parameters:
            s+= p.__str__() +","

        s = s[:-1] + ")"
        s+= self.body.__str__()
        return s

    def xml(self,ob=className):
        s = self.toxml(ob)
        s += super().xml()
        for p in self.parameters:
            s+= p.xml()
        s+= self.body.xml()
        s+= self.toxml(ob,True)
        return s

class FnParameter(VariableDeclaration):
    className = "FnParameter"

    def __init__(self, tp:Token, name, isArray=False):
        super().__init__(tp,name)
        self.isArray = isArray

    def xml(self,ob=className):
        s = self.toxml(ob)
        s+= super().xml()
        s+= self.toxml(ob,True)
        return s

class Statement(AST):
    className = "Statement"

    def __init__(self):
        super().__init__()
        self.node = None
        self.deleteMe = False

    def __str__(self):
        print(self.node)

    def xml(self,ob=className):
        s=self.toxml(ob)
        if self.deleteMe:
            s+="DELETE ME"
        if self.node is not None:
            s+= self.node.xml()
        s+=self.toxml(ob,True)
        return s

class ReturnStatement(Statement):
    className = "ReturnStatement"

    def __init__(self,value):
        super().__init__()
        self.node = value

    def xml(self, ob=className):
        s = super().xml(ob)
        return s

class BreakStatement(Statement):
    className = "BreakStatement"

    def __init__(self):
        super().__init__()

    def xml(self, ob=className):
        s = super().xml(ob)
        return s

class ContinueStatement(Statement):
    className = "ContinueStatement"

    def __init__(self):
        super().__init__()

    def xml(self, ob=className):
        s = super().xml(ob)
        return s

class EXP(AST):
    className = "EXP"
    def __init__(self):
        super().__init__()
        self.negation = False

    def toxml(self,ob = None, end = False)->str:
        if ob is not None:
            return wrapxml(ob,end)
        else:
            return wrapxml(self.className, end)

class WhileLoop(Statement):
    className = "WhileLoop"

    def __init__(self,condition:EXP,block:Block):
        super().__init__()
        self.condition = condition
        self.node = block

    def xml(self,ob=className):
        s = self.toxml(ob)
        s += "While" + self.condition.xml()+ "do"
        s += self.node.xml()
        s += self.toxml(ob,True)
        return s

class ForLoop(WhileLoop):
    className = "ForLoop"

    def __init__(self, condition:EXP, block:Block,var:Statement = None,incrementStatement:Statement=None):
        super().__init__(condition, block)
        self.var = var
        self.incrementStatement = incrementStatement

    def xml(self,ob=className):
        s = self.toxml(ob)
        s += self.var.xml()
        s += self.incrementStatement.xml()
        s += "For" + self.condition.xml()+ "do"

        s += self.node.xml()
        s += self.toxml(ob,True)
        return s

class IfStatement(Statement):
    className = "IfStatement"

    def __init__(self, condition: EXP):
        super().__init__()
        self.condition = [condition]
        self.blocks = []
        self.containsElse = False

    def xml(self, ob=className):
        s = self.toxml(ob)
        i = 0
        s += "if" + self.condition[0].xml() + "do"
        s += self.blocks[0].xml()
        if self.blocks.__len__()>1:
            lastIndex = self.condition.__len__()
            for i in range(1,lastIndex):
                s += "elif" + self.condition[i].xml() + "do"
                s += self.blocks[i].xml()

        if self.containsElse:
            s += "else do" + self.blocks[self.blocks.__len__()-1].xml()
        s += self.toxml(ob, True)
        return s

class Literall(EXP):
    className = "Literall"

    def __init__(self, token: Token):
        super().__init__()
        self.token = token

    def getValue(self):
        return self.token.value

    def __str__(self):
        return str(self.token.value)

    def xml(self,ob=className):
        return self.toxml(ob)+str(self.token.value)+self.toxml(ob,True)

class Integer(Literall):
    className = "Int_Const"

    def __init__(self, token:Token):
        super().__init__(token)

    def xml(self,ob=className):
        return self.toxml(ob)+str(self.token.value)+self.toxml(ob,True)

class Float(Integer):
    className = "Float_Const"

    def __init__(self, token:Token):
        super().__init__(token)

    def xml(self,ob=className):
        return self.toxml(ob)+str(self.token.value)+self.toxml(ob,True)

class String(Literall):
    className = "String_const"

    def __init__(self, token:Token):
        super().__init__(token)

    def xml(self,ob=className):
        return self.toxml(ob)+str(self.token.value)+self.toxml(ob,True)

class Boolean(Literall):
    className = "Bool_const"

    def __init__(self, token:Token):
        super().__init__(token)

    def xml(self,ob=className):
        return self.toxml(ob)+str(self.token.value)+self.toxml(ob,True)

class Null(Literall):
    className = "Null_const"

    def __init__(self, token:Token):
        super().__init__(token)

    def xml(self,ob=className):
        return self.toxml(ob)+str(self.token.value)+self.toxml(ob,True)

    @staticmethod
    def create():
        return Null(Token(LexName.NULL,None))

class BinaryOperator(EXP):

    className = "BinaryOperator"

    def __init__(self, left: AST, op: Token, right: AST):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right
        self.negation = False

    def __str__(self):
        return  "("+str(self.left) + str(self.op.value) + str(self.right)+")"

    def xml(self,ob=className):
        s=""
        if self.negation:
            s += self.toxml("NOT")
        s += self.toxml(ob)


        s += str(self.left.xml())
        s += str(self.op.type)
        s += str(self.right.xml())
        s+= self.toxml(ob,True)
        if self.negation:
            s += self.toxml("NOT",True)
        return s

class ValueCall(EXP):
    className = "ValueCall"

    def __init__(self, name):
        super().__init__()
        self.name = name

    def xml(self,ob=className):
        s = ""
        if self.negation:
            s += self.toxml("NOT")
        s+=self.toxml(ob)+str(self.name)+self.toxml(ob,True)
        if self.negation:
            s += self.toxml("NOT",True)
        return s

class VariableAssign(ValueCall):
    className = "VariableAssign"

    def __init__(self, name,operator:Token, value:AST):
        super().__init__(name)
        self.value = value
        self.operator = operator

    def xml(self,ob=className):
        s = self.toxml(ob)
        s+= super().xml()
        s+= self.value.xml()
        s+= self.toxml(ob,True)
        return s

class ArrayElementAssign(VariableAssign):
    className = "ArrayElementAssign"

    def __init__(self, name, operator: Token, value: AST, index:AST):
        super().__init__(name,operator,value)
        self.index = index

    def xml(self, ob=className):
        s = self.toxml(ob)
        s += super().xml()
        s += self.value.xml()
        s += self.index.xml()
        s += self.toxml(ob, True)
        return s

class FunctionCall(ValueCall):
    className = "FunctionCall"

    def __init__(self, name, parameters: list):
        super().__init__(name)
        self.parameters = parameters

    def xml(self,ob=className):
        s = self.toxml(ob)
        s += super().xml()
        s += self.toxml("Arguments")
        for p in self.parameters:
            s += self.toxml("Arg")
            s += p.xml()
            s += self.toxml("Arg",True)
        s += self.toxml("Arguments",True)
        s += self.toxml(ob, True)
        return s

class ArrayCall(ValueCall):
    className = "ArrayCall"

    def __init__(self, name, index):
        super().__init__(name)
        self.index = index

    def xml(self, ob=className):
        s = self.toxml(ob)
        s+= super().xml()
        s+= self.index.xml()
        s += self.toxml(ob, True)
        return s

class PrintCall(FunctionCall):
    className = "PrintCall"

    def __init__(self, name, parameters: list):
        super().__init__(name, parameters)

    def xml(self,ob=className):
        return super().xml(ob)

class InputCall(FunctionCall):
    className = "PrintCall"

    def __init__(self, name, parameters: list):
        super().__init__(name, parameters)

    def xml(self,ob=className):
        return super().xml(ob)