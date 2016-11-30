import math

from src.ASTnodes import *
from src.LexNames import LexName
from src.lexer import Token, Pos


class ParserException(Exception):
    def __init__(self,*args):
        super().__init__(args)



class Parser:
    __fixingRange = 1
    __maxSemiInsertionCount = 3

    def __init__(self,tokenList:list):
        self.tokenList = tokenList
        self.tokenNo = 0
        self.lastInsertedToken = None
        self.timesInsertedSemi = 0
        self.needReparse = False
        self.errorToken = None

    def makeNewPosition(self,prevToken):
        nextToken = None
        try:
            nextToken = self.tokenList[self.tokenNo+1]
        except Exception:
            pass
        pos = None
        if nextToken is not None:
            pos = Pos(int(math.ceil(prevToken.position.linePos+nextToken.position.linePos)/2),
                      (prevToken.position.indexPos + nextToken.position.indexPos) // 2)
        else:
            pos = Pos(prevToken.position.linePos,prevToken.position.indexPos+1)
        return pos

    def delCurrentToken(self):
        del self.tokenList[self.tokenNo]

    def getNextToken(self):
        self.tokenNo+=1
        return self.tokenList[self.tokenNo]

    def getPrevTokenType(self):
        token = LexName.ESC
        try:
            token = self.tokenList[self.tokenNo-1].type
        except Exception:
            pass
        return token

    def getPrevToken(self):
        token = LexName.ESC
        try:
            token = self.tokenList[self.tokenNo - 1]
        except Exception:
            pass
        return token


    def getCurrTokenType(self):
        return self.tokenList[self.tokenNo].type

    def getCurrToken(self):
        return self.tokenList[self.tokenNo]

    def error(self,expected = ""):
        got = self.getCurrToken()
        raise ParserException("Expected = "+str(expected) + " got = "+ str(got))

    def tryToFix(self,expectedToken,tryNo:int=0):

        #try to delete unopened blocks
        if not self.countBlocks():
            if self.getCurrTokenType() in LexName.RightClose:
                self.delCurrentToken()
                return "DELETE"

        #fix is only available, if we have expectedToken
        if tryNo == 0:
            self.errorToken = self.getCurrToken()
            #try to insert it
            if expectedToken == LexName.SEMI:
                self.timesInsertedSemi+=1
            if self.timesInsertedSemi > self.__maxSemiInsertionCount:
                raise ParserException("Possible infinite loop, terminating",self.errorToken)
            self.tokenList.insert(self.tokenNo,Token(expectedToken,None,self.makeNewPosition(self.getPrevToken())))
            self.lastInsertedToken = expectedToken
            return "INSERT"
        elif tryNo == 1:
            #try to replace it
            self.tokenList.pop(self.tokenNo)
            self.tokenList[self.tokenNo] = Token(expectedToken,None,self.makeNewPosition(self.getPrevToken()))
            return "REPLACE"
        elif tryNo >=2:
            return "FAIL"


    def eat(self,tokenType=None,attempt:int=0):
        if tokenType != LexName.SEMI:
            self.timesInsertedSemi = 0
        if tokenType is None:
            self.getNextToken()
            return True
        if self.getCurrTokenType() == tokenType:
            self.getNextToken()
            return True
        else:
            res = self.tryToFix(tokenType,attempt)
            if res == "DELETE":
                return "DELETE"
            elif res == "INSERT":
                eaten = self.eat(tokenType,attempt+1)
            else:
                return "FAIL"
            if eaten=="FAIL" and attempt == 0:
                self.error(tokenType)

    def root(self):
        self.tokenNo = 0
        root = Root()
        while self.getCurrTokenType()!= LexName.EOF:
            root.statements.append(self.statement())
        return root

    def block(self):
        self.eat(LexName.BLOCKL)
        node = self.blockBody()
        self.eat(LexName.BLOCKR)
        return node

    def blockBody(self):
        statements = []
        while self.getCurrTokenType() != LexName.BLOCKR:
            statements.append(self.statement())

        block = Block()
        block.statements = statements
        return block

    def statement(self):
        statement = Statement()

        node = None
        if self.getCurrTokenType() == LexName.BLOCKL:
            node = self.block()
            statement.node = node
            return statement
        elif self.getCurrTokenType() == LexName.VALUECALL:
            node = self.valueCall()
        elif self.getCurrTokenType() == LexName.DEF:
            node = self.functionDefinition()
        elif self.getCurrTokenType() in LexName.Types:
            node = self.variableDeclaration()
        elif self.getCurrTokenType() in LexName.ExitStatements:
            node = self.exitStatement()
        elif self.getCurrTokenType() in LexName.FlowStatements:
            node = self.flowStatement()
        else:
            node = self.exp1()
        statement.node = node
        if self.eat(LexName.SEMI) == "DELETE":
            self.needReparse = True

        return statement

    def exp1(self):
        node = self.exp2()
        while self.getCurrTokenType() in LexName.LogicOperators:
            token = self.getCurrToken()
            if token.type == LexName.AND:
                self.eat()
            elif token.type == LexName.OR:
                self.eat()

            node = BinaryOperator(node, token, self.exp2())

        return node

    def exp2(self):
        node = self.exp3()

        while self.getCurrTokenType() in LexName.CompareOperators:
            token = self.getCurrToken()
            self.eat()
            node = BinaryOperator(node, token, self.exp3())

        return node

    def exp3(self):
        node = self.term()
        while self.getCurrTokenType() in [LexName.PLUS,LexName.MINUS]:
            token = self.getCurrToken()
            self.eat()
            node = BinaryOperator(node, token, self.term())

        return node

    def term(self):
        node = self.factor()

        while self.getCurrTokenType() in [LexName.MULTIPLY,LexName.DIVIDE]:
            token = self.getCurrToken()
            self.eat()
            node = BinaryOperator(node, token, self.factor())

        return node

    def factor(self):
        token = self.getCurrToken()
        node = AST()
        if token.type == LexName.INTEGER_CONST:
            self.eat()
            node = Integer(token)
        elif token.type == LexName.FLOAT_CONST:
            self.eat()
            node = Float(token)
        elif token.type == LexName.NULL:
            self.eat()
            node = Null(token)
        elif token.type == LexName.STRING_CONST:
            self.eat()
            node = String(token)
        elif token.type in [LexName.TRUE,LexName.FALSE]:
            self.eat()
            node = Boolean(token)
        elif token.type in [LexName.VALUECALL,LexName.PRINT,LexName.INPUT]:
            node = self.valueCall()
        elif token.type == LexName.PARENTHISISL:
            self.eat()
            node = self.exp1()
            self.eat(LexName.PARENTHISISR)
        elif token.type == LexName.NOT:
            self.eat()
            node = self.exp1()
            node.negation = True
        else:
            # node is empty
            node.isEmpty = True
        return node

    def valueCall(self):
        node = None
        name = self.getCurrToken().value
        self.eat()
        if self.getCurrTokenType() == LexName.PRINT:
            node = self.functionCall(name)
            self.eat(LexName.PARENTHISISR)
            node = PrintStatement(node.name,node.parameters)
        elif self.getCurrTokenType() == LexName.INPUT:
            node = self.functionCall(name)
            self.eat(LexName.PARENTHISISR)
            node = InputStatement(node.name, node.parameters)
        elif self.getCurrTokenType() == LexName.PARENTHISISL:
            #funcionCall
            self.eat()
            node = self.functionCall(name)
            self.eat(LexName.PARENTHISISR)
        elif self.getCurrTokenType() == LexName.BRACKETL:
            # arrayCall
            self.eat()
            index = self.exp1()
            self.eat(LexName.BRACKETR)
            node = ArrayCall(name,index)
        else:
            # variableCall
            value = None
            if (self.getCurrTokenType() in LexName.CompareOperators):
                self.delCurrentToken()
                self.tokenList.insert(self.tokenNo, Token(LexName.ASSIGN, None,self.getPrevToken().pos))
            if self.getCurrTokenType() == LexName.ASSIGN or self.getCurrTokenType() in LexName.AdvancedAssign:
                token = self.getCurrToken()
                self.eat()
                value = self.exp1()
                node = VariableAssign(name,token, value)
            else:
                #simpleValueCall
                node = ValueCall(name)

        return node

    def functionDefinition(self):
        self.eat(LexName.DEF)

        token = self.getCurrToken()
        name = None
        parameters = list()
        tp = None
        body = None

        if self.getCurrTokenType() in LexName.Types:
            tp = Type(self.getCurrTokenType())
            self.eat()
            if self.getCurrTokenType() == LexName.VALUECALL:

                name = self.getCurrToken().value

                self.eat()
                self.eat(LexName.PARENTHISISL)

                while self.getCurrTokenType() != LexName.PARENTHISISR:
                    parameters.append(self.functionParameter())
                    if self.getCurrTokenType() == LexName.PARENTHISISR:
                        break
                    self.eat(LexName.COMMA)
                    if self.getCurrTokenType() == LexName.PARENTHISISR:
                        self.tokenNo-=1
                        self.delCurrentToken()
                self.eat()
                body = self.block()
                return FunctionDeclaration(tp,name,parameters,body)
            else:
                self.error()

    def functionCall(self,name):
        parameters = list()
        if self.getCurrTokenType() != LexName.PARENTHISISR:
            parameters.append(self.exp1())
            while self.getCurrTokenType() != LexName.PARENTHISISR:
                self.eat(LexName.COMMA)
                parameters.append(self.exp1())
        return FunctionCall(name,parameters)

    def functionParameter(self):

        if self.getCurrTokenType() in LexName.Types:
            tp = self.getCurrTokenType()
            isArray = False
            self.eat()
            if self.getCurrTokenType() == LexName.BRACKETL:
                self.eat()
                self.eat(LexName.BRACKETR)
                isArray = True
            name = self.getCurrToken().value
            self.eat(LexName.VALUECALL)
            return FnParameter(tp,name,isArray)

    def assign(self,node:VariableAssign):
        if (self.getCurrTokenType() in LexName.CompareOperators) or (self.getCurrTokenType() in LexName.AdvancedAssign):
            self.delCurrentToken()
            self.tokenList.insert(self.tokenNo,Token(LexName.ASSIGN,None,self.makeNewPosition(self.getPrevToken())))
        if self.getCurrTokenType() == LexName.ASSIGN:
            self.eat()
            value = self.exp1()
            node.value = value
        return node


    def variableDeclaration(self):
        tp = self.getCurrToken().type
        self.eat()
        size = None
        if self.getCurrTokenType() == LexName.BRACKETL:
            self.eat()
            size = self.exp1()
            self.eat(LexName.BRACKETR)
        name = self.getCurrToken().value
        self.eat(LexName.VALUECALL)
        if size is not None:
            return ArrayDeclaration(tp,name,size)

        value = None
        if (self.getCurrTokenType() in LexName.CompareOperators) or (self.getCurrTokenType() in LexName.AdvancedAssign):
            self.delCurrentToken()
            self.tokenList.insert(self.tokenNo,Token(LexName.ASSIGN,None,self.makeNewPosition(self.getPrevToken())))
        if self.getCurrTokenType() == LexName.ASSIGN:
            self.eat()
            value = self.exp1()
        return VariableInitialization(tp,name,value)

    def exitStatement(self):
        node = None
        tokenType = self.getCurrTokenType()
        self.eat()
        if tokenType == LexName.CONTINUE:
            node = ContinueStatement()
        elif tokenType == LexName.BREAK:
            node = BreakStatement()
        else:
            node = ReturnStatement(self.exp1())
        return node

    def flowStatement(self):
        node = None
        tokenType = self.getCurrTokenType()
        self.eat()
        self.eat(LexName.PARENTHISISL)
        if tokenType == LexName.WHILE:
            exp = self.exp1()
            self.eat(LexName.PARENTHISISR)
            block = self.statement()
            node = WhileLoop(exp,block)
        elif tokenType == LexName.FOR:

            var = self.statement()
            condition = self.statement()
            increment = self.statement()
            self.eat(LexName.PARENTHISISR)

            block = self.statement()
            node = ForLoop(condition,block,var,increment)
        else:
            node = IfStatement(self.exp1())
            self.eat(LexName.PARENTHISISR)

            node.blocks.append(self.statement())
            if self.getCurrTokenType() == LexName.ELSE:
                self.eat()
                node.blocks.append(self.statement())
        return node

    def countBlocks(self):
        lefties = [LexName.PARENTHISISL,LexName.BRACKETL,LexName.BLOCKL]
        righties = [LexName.PARENTHISISR,LexName.BRACKETR,LexName.BLOCKR]
        countL = 0
        countR = 0
        for token in self.tokenList:
            if token.type in lefties:
                countL+=1
            elif token.type in righties:
                countR+=1
        return countL==countR


