from src.lexer import Token


class Parser:
    types = ["STRING", "BOOLEAN", "INT", "FLOAT"]

    def __init__(self,tokenList:list):
        self.tokenList = tokenList
        self.currToken = tokenList[0]
        self.tokenNo = 0

    def getNextToken(self):
        self.tokenNo+=1
        return self.tokenList[self.tokenNo]

    def getCurrTokenType(self):
        return self.currToken.type

    def error(self):
        raise Exception("Error")

    def eat(self,tokenType=None):
        if tokenType is None:
            tokenType = self.currToken.type

        if self.currToken.type == tokenType:
            self.currToken = self.getNextToken()
        else:
            self.error()

    def root(self):
        root = Root()
        while self.getCurrTokenType()!= "EOF":
            root.statements.append(self.statement())
        return root

    def block(self):
        self.eat("BLOCKL")
        node = self.blockBody()
        self.eat("BLOCKR")
        return node

    def blockBody(self):
        statemets = list()
        while self.getCurrTokenType() != "BLOCKR":
            statemets.append(self.statement())
        block = Block()
        block.statements = statemets
        return block

    def statement(self):
        node = None
        if self.getCurrTokenType() == "BLOCKL":
            node = self.block()
        elif self.getCurrTokenType() == "VARIABLE":
            node = self.variable()
        elif self.getCurrTokenType() == "DEF":
            node = self.functionDefinition()
        elif self.getCurrTokenType() in Parser.types:
            node = self.variableDeclaration()
        else:

            node = self.exp1()
        self.eat("SEMI")
        return node



    def exp1(self):
        node = self.exp3()
        while self.currToken.type in ["AND", "OR"]:
            token = self.currToken
            if token.type == "AND":
                self.eat()
            elif token.type == "OR":
                self.eat()

            node = BinaryOperator(node, token, self.factor())

        return node

    def exp2(self):
        node = self.exp2()
        array = ["EQUALS", "GREATER", "LESSEQUAL", "LESS", "GREATEREQUAL", "NOTEQUAL"]
        while self.currToken.type in array:
            token = self.currToken
            self.eat()
            node = BinaryOperator(node, token, self.factor())

        return node

    def exp3(self):
        node = self.term()
        while self.currToken.type in ["PLUS","MINUS"]:
            token = self.currToken
            self.eat()
            node = BinaryOperator(node, token, self.factor())

        return node

    def term(self):
        node = self.factor()

        while self.currToken.type in ["MULTIPLY","DIVIDE"]:
            token = self.currToken
            self.eat()
            node = BinaryOperator(node, token, self.factor())

        return node

    def factor(self):
        token = self.currToken
        node = None
        if token.type == "INTEGER_CONST":
            self.eat()
            node = Integer(token)
        elif token.type == "FLOAT_CONST":
            self.eat()
            node = Float(token)
        elif token.type == "NULL":
            self.eat()
            node = Null(token)
        elif token.type == "STRING_CONST":
            self.eat()
            node = String(token)
        elif token.type in ["TRUE","FALSE"]:
            self.eat()
            node = Boolean(token)
        elif token.type == "VARIABLE":
            node = self.variable()
        elif token.type == "PARENTHISISL":
            self.eat()
            node = self.exp1()
            self.eat("PARENTHISISR")
        elif token.type == "NOT":
            self.eat()
            node = self.exp1()
        #    add negation property
        return node


    def variable(self):
        name = self.currToken.value
        self.eat()
        if self.getCurrTokenType() == "PARENTHISISL":
            self.eat()
            token = self.functionCall(name)
            self.eat("PARENTHISISR")
        elif self.getCurrTokenType() == "BRACKETL":
            self.eat()
            token = self.exp1()
            self.eat("BRACKETR")
        else:
            pass

    def functionDefinition(self):
        self.eat("DEF")

        token = self.currToken
        name = None
        parameters = list()
        tp = None
        body = None

        if self.getCurrTokenType() in Parser.types:
            tp = Type(self.getCurrTokenType())
            self.eat()
            if self.getCurrTokenType() == "VARIABLE":

                name = self.currToken.value

                self.eat()
                self.eat("PARENTHISISL")

                while self.getCurrTokenType() != "PARENTHISISR":
                    parameters.append(self.functionParameter())
                    if self.getCurrTokenType() == "PARENTHISISR":
                        break
                    self.eat("COMMA")
                self.eat()
                body = self.block()
                return FunctionDeclaration(tp,name,parameters,body)
            else:
                self.error()



    def functionCall(self,name):
        parameters = list()
        parameters.append(self.exp1())
        while self.currToken.type != "PARENTHISISR":
            self.eat("COMMA")
            parameters.append(self.exp1())
        return FunctionCall(name,parameters)


    def functionParameter(self):

        if self.getCurrTokenType() in Parser.types:
            tp = self.getCurrTokenType()
            isArray = False
            self.eat()
            if self.getCurrTokenType() == "BRACKETL":
                self.eat()
                self.eat("BRACKETR")
                isArray = True
            name = self.currToken.value
            self.eat("VARIABLE")
            return FnParameter(tp,name,isArray)

    def arrayCall(self):
        name = self.currToken.value
        self.eat("VARIABLE")
        self.eat("BRACKETL")
        index = self.exp1()
        self.eat("BRACKETR")
        return ArrayCall(name,index)

    def variableDeclaration(self):
        tp = self.currToken.type
        self.eat()
        size = None
        if self.getCurrTokenType() == "BRACKETL":
            self.eat()
            size = self.exp1()
            self.eat("BRACKETR")
        name = self.currToken.value
        self.eat("VARIABLE")
        if size is not None:
            return ArrayDeclaration(tp,name,size)

        value = None
        if self.getCurrTokenType() == "ASSIGN":
            self.eat()
            value = self.exp1()
        return VariableInitialization(tp,name,value)


class AST:
    def __str__(self):
        return ""

class Block(AST):
    def __init__(self):
        self.statements = list()

    def __str__(self):
        s = "{\n"
        for st in self.statements:
            s+=st.__str__()+";\n"
        return s+"}"

class Root(Block):
    def __init__(self):
        super().__init__()



class Statement(AST):
    def __init__(self):
        self.nodes = list()

    def __str__(self):
        for n in self.nodes:
            print(n)


class InlineStatement(Statement):
    pass

class SimpleStatement(Statement):
    pass



class Type(AST):
    def __init__(self,tp,isArray=False):
        self.type = tp
        self.isArray = isArray

    def __str__(self):
        s = str(self.type)
        if self.isArray:
            s+="[]"
        return s


class VariableDeclaration(Type):
    def __init__(self, tp, name):
        super().__init__(tp)
        self.name = name

    def __str__(self):
        s = str(self.type)
        if self.isArray:
            s += "[]"
        return s + " "+str(self.name)


class VariableInitialization(VariableDeclaration):
    def __init__(self, tp, name, value=None):
        super().__init__(tp,name)
        self.value = value

    def __str__(self):
        s = str(self.type)
        if self.isArray:
            s += "[]"
        return s + " "+str(self.name)+" = "+str(self.value)

class ConstantDeclaration(VariableDeclaration):
    pass

class ArrayDeclaration(VariableDeclaration):
    def __init__(self, tp, name, size):
        super().__init__(tp, name)
        self.value = [None] *size
        self.size = size


class FunctionDeclaration(VariableDeclaration):
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




class FnParameter(VariableDeclaration):
    def __init__(self, tp, name, isArray=False):
        super().__init__(tp,name)
        self.name = name
        self.isArray = isArray
class Name(AST):
    def __init__(self,name):
        self.name = name
class Variable(Name):
    def __init__(self, name):
        super().__init__(name)

class ArrayCall(Variable):
    def __init__(self, name, index):
        super().__init__(name)
        self.index = index

class IOStatement(Statement):
    pass

class PrintStatement(IOStatement):
    pass

class InputStatement(IOStatement):
    pass

class ExitStatement(SimpleStatement):
    pass

class ReturnStatement(ExitStatement):
    pass

class BreakStatement(ExitStatement):
    pass

class ContinueStatement(ExitStatement):
    pass

class FlowStatement(SimpleStatement):
    pass

class WhileLoop(FlowStatement):
    pass

class ForLoop(WhileLoop):
    pass

class IfStatement(FlowStatement):
    pass

class Literall(AST):

    def __init__(self,token:Token):
        self.token = token

    def getValue(self):
        return self.token.value

    def __str__(self):
        return str(self.token.value)

class Integer(Literall):
    def __init__(self, token:Token):
        super().__init__(token)


class Float(Integer):
    def __init__(self, token:Token):
        super().__init__(token)


class String(Literall):
    def __init__(self, token:Token):
        super().__init__(token)

class Boolean(Literall):
    def __init__(self, token:Token):
        super().__init__(token)

class Null(Literall):
    def __init__(self, token:Token):
        super().__init__(token)

class BinaryOperator(AST):
    def __init__(self,left:Token,op:Token,right:Token):
        self.left = left
        self.op = op
        self.right = right

    def __str__(self):
        return  str(self.left) +"BO"+ str(self.op.value) + str(self.right)

class FunctionCall(AST):
    def __init__(self,name,parameters:list):
        self.name = name
        self.paramaters = parameters.copy()
