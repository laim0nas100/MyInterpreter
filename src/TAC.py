from definitions import SemanticException
from src.ASTnodes import *
from src.LexNames import LexName
from src.SpecificTypes import Scope, TVariable, TAC, Tnames
from src.SpecificTypes import TFunction
from src.lib import ArrayList, OrderedMap











class TACgen:
    def __init__(self):
        self.scopes = OrderedMap()
        self.currentBlockLabel = None
        self.currentBlock = None
        self.continueLabel = ArrayList(None,None)
        self.breakLabel = ArrayList(None,None)
        self.rootLabel = "0B"
        self.functionStack = ""
        self.currentFunction = ArrayList(None,None)
        self.currentFunctionName = ArrayList(None,None)
        self.returnWasDeclared = ArrayList(None,None)

    def makeTmp(self,index: int):
        return "_r" + str(index)
    
    def nameIsDefined(self,startingLabel:str,name:str,function=False,checkOnlyLocal=False):

        childScope = self.scopes.get(startingLabel)
        if checkOnlyLocal:
            if function is True:
                return childScope.functions.containsKey(name)
            else:
                return childScope.variables.containsKey(name)
        if childScope is not None:

            if function is True:
                if childScope.functions.containsKey(name):
                    return True
                else:
                    return self.nameIsDefined(childScope.getParentLabel(),name,True)
            else:
                if childScope.variables.containsKey(name):
                    return True
                else:
                    return self.nameIsDefined(childScope.getParentLabel(),name,function)
        else:
            return False

    def getOrderedListOfStatements(self,scopeLabel):

        statements = []
        scope = self.scopes.get(scopeLabel)
        if scope is None:
            print(scopeLabel+"is none")
            return statements
        i = 0
        for st in scope.statements:
            if st.operation == Tnames.LABEL:
                if i == 0:
                    statements.append(st)
                elif st.tuple[1] !=scope.label:
                    if str.startswith(st.tuple[1],"E"):
                        statements.append(st)
                    else:
                        statements.extend(self.getOrderedListOfStatements(st.tuple[1]))
                else:
                    statements.append(st)
            else:
                statements.append(st)
            i += 1
        return statements



    @staticmethod
    def getTabbedStatements(statements):
        printable = []
        tabLimit = 0
        for statement in statements:
            line = statement.__str__()
            for i in range(0,tabLimit):
                line = "\t"+line
            if statement.tuple[0] == Tnames.LABEL:
                if str.startswith(statement.tuple[1], "E"):
                    tabLimit -= 1
                else:
                    tabLimit += 1
                    line = "\t" + line

            printable.append(line)
        return printable

    def getStatementsAsString(self):
        statements = []
        for key in self.scopes.keyOrder:

            scope = self.scopes.get(key)
            string = "Block:" + scope.label
            if scope.functionName:
                string +=" def "+scope.functionName
            statements.append(string)
            for statement in scope.statements:
                statements.append(statement.__str__())
            statements.append("")
        return statements

    def getCurrentBlockEndLabel(self):
        return "E"+self.currentBlockLabel

    def scopeIsPresent(self,label):
        return self.scopes.containsKey(label)

    def updateCurrentBlock(self,label):
        self.currentBlockLabel = label
        self.currentBlock = self.scopes.get(label)

    def parseRoot(self,block:Root):
        scope = Scope(block.label)
        scope.functions.put("print",TFunction([LexName.NULL,False], "print","0B", []))
        scope.functions.put("input",TFunction([LexName.STRING,False], "input","0B", []))
        self.scopes.put(block.label,scope)
        self.parseBlock(block)

    def parseBlock(self,block:Block,putLabel=True):
        scope = Scope(block.label)
        self.updateCurrentBlock(block.label)
        if self.scopes.containsKey(block.label):
            scope = self.scopes.get(scope.label)
        else:
            self.scopes.put(scope.label,scope)
        if putLabel:
            scope.statements.append(TAC(Tnames.LABEL,scope.label))
        for st in block.statements:
            self.currentBlockLabel = scope.label
            scope.statements.extend(self.parseStatement(st))
        if putLabel:
            scope.statements.append(TAC(Tnames.LABEL,block.exitLabel()))
        self.scopes.put(scope.label, scope)

    def parseStatement(self,statement:Statement):
        statements = list()
        scope = self.scopes.get(self.currentBlockLabel)
        if isinstance(statement,Statement):
            node = statement.node

            if isinstance(node,VariableAssign):
                if not self.nameIsDefined(scope.label,node.name):
                    raise SemanticException(node.name + " Was not yet defined in "+scope.label)
                if isinstance(node,ArrayElementAssign):
                    statements.extend(self.parseArrayElementAssign(node))
                else:
                    statements.extend(self.untangleExpression(node.value))
                    statements.append(TAC(node.operator.type, node.name, self.makeTmp(0)))
            elif isinstance(node,VariableDeclaration):
                if isinstance(node, FunctionDeclaration):
                    label = scope.label
                    self.parseDefineFunction(node)
                    self.updateCurrentBlock(label)
                else:


                    if isinstance(node,VariableInitialization):
                        if self.nameIsDefined(scope.label, node.name, checkOnlyLocal=True):
                            raise SemanticException(node.name + " Is allready defined in this scope")
                        else:
                            scope.variables.put(node.name, TVariable([node.tp, False], node.name))
                        statements.extend(self.untangleExpression(node.value))
                        statements.append(TAC(Tnames.INIT,[node.tp,node.name],self.makeTmp(0)))
                    elif isinstance(node,ArrayDeclaration):
                        if self.nameIsDefined(scope.label, node.name, checkOnlyLocal=True):
                            raise SemanticException(node.name + " Is allready defined in this scope")
                        else:
                            scope.variables.put(node.name, TVariable([node.tp, True], node.name))
                        statements.extend(self.untangleExpression(node.size))
                        statements.append(TAC(Tnames.INITARR,self.makeTmp(0), [node.tp, node.name]))
                    else:
                        statements.append(TAC(Tnames.INIT,node.name, Null(Token(LexName.NULL,None))))
            elif isinstance(node,WhileLoop):
                statements.append(TAC(Tnames.CALLBLOCK,node.node.label))
                if isinstance(node, ForLoop):
                    self.parseFor(node)
                else:
                    self.parseWhile(node)
            elif isinstance(node,Block):
                statements.append(TAC(Tnames.CALLBLOCK,node.label))
                self.parseBlock(node)
            elif isinstance(node,ReturnStatement):
                statements.extend(self.untangleExpression(node.node))
                statements.append(TAC(Tnames.PUSH,self.makeTmp(0)))
                statements.append(TAC(Tnames.RETURN,self.currentFunction.getLast(),self.currentFunctionName.getLast()))
                self.returnWasDeclared.pop()
                self.returnWasDeclared.append(True)
            elif isinstance(node,BreakStatement):
                if self.breakLabel is not None:
                    statements.append(TAC(Tnames.JUMP,self.breakLabel.getLast()))
            elif isinstance(node,ContinueStatement):
                if self.continueLabel is not None:
                    statements.append(TAC(Tnames.JUMP,self.continueLabel.getLast()))
            elif isinstance(node,IfStatement):
                statements.append(TAC(Tnames.CALLBLOCK,node.blocks[0].label))
                self.parseIf(node)
            elif isinstance(node,EXP):
                statements.extend(self.untangleExpression(node))
        return statements

    def parseDefineFunction(self,node:FunctionDeclaration):

        functionScope = Scope(node.body.label)
        functionScope.functionName = node.name
        function = TFunction([node.tp,node.isArray], node.name,node.body.label, node.parameters)
        self.scopes.put(functionScope.label, functionScope)
        # self.updateCurrentBlock(functionScope.label)
        if self.nameIsDefined(functionScope.label,functionScope.functionName,function=True):
            raise SemanticException("Function name "+functionScope.functionName+" allready defined" )
        else:

            parentScope = self.scopes.get(functionScope.getParentLabel())
            parentScope.functions.put(functionScope.functionName,function)
            functionScope.functions.put(functionScope.functionName,function)
            #parentScope.statements.append(TAC(Tnames.,functionScope.label))

        for p in node.parameters:
            if self.nameIsDefined(functionScope.label, p.name, checkOnlyLocal=True):
                raise SemanticException(p.name + " Is allready defined in "+ functionScope.label+" scope")
            else:
                functionScope.variables.put(p.name, TVariable([p.tp, p.isArray], p.name))
        self.updateCurrentBlock(functionScope.getParentLabel())
        self.functionStack += "f"
        self.currentFunction.append(functionScope.label)
        self.currentFunctionName.append(functionScope.functionName)
        self.returnWasDeclared.append(False)
        self.parseBlock(node.body)

        #popping variables from stack
        for p in node.parameters:
            functionScope.statements.insert(1,TAC("POP", self.makeTmp(0)))
            functionScope.statements.insert(2, TAC(LexName.ASSIGN, p.name, self.makeTmp(0)))
        functionScope.statements.append(TAC(Tnames.LOAD,self.makeTmp(0),[LexName.NULL,""]))
        functionScope.statements.append(TAC(Tnames.PUSH, self.makeTmp(0)))
        functionScope.statements.append(TAC(Tnames.RETURN, self.currentFunction.getLast(),self.currentFunctionName.getLast()))
        self.currentFunction.pop()
        self.currentFunctionName.pop()
        if not self.returnWasDeclared.pop():
            raise SemanticException("Return was not declared in function "+function.name)
        self.functionStack = self.functionStack[:-1]

    def parseArrayElementAssign(self,node:ArrayElementAssign):
        statements = []
        statements.extend(self.untangleExpression(node.value))
        statements.append(TAC(Tnames.PUSH, self.makeTmp(0)))
        #_t1 = index, _t0 = value
        statements.extend(self.untangleExpression(node.index))
        statements.append(TAC(Tnames.LOAD,self.makeTmp(1),self.makeTmp(0)))
        statements.append(TAC(Tnames.POP,self.makeTmp(0)))
        statements.append(TAC(node.operator.type,[node.name,self.makeTmp(1)],self.makeTmp(0)))
        return statements

    def parseFor(self,loop:ForLoop):
        label = loop.node.label

        scope = Scope(label)
        self.scopes.put(label,scope)
        self.updateCurrentBlock(label)
        statsBefore = ArrayList()
        statsBefore.extend(self.parseStatement(loop.var))
        statsAfter = ArrayList()
        statsAfter.append(TAC(Tnames.LABEL,"C"+scope.label))
        statsAfter.extend(self.parseStatement(loop.incrementStatement))

        self.parseWhile(loop, False)
        scope = self.scopes.get(label)
        statsBefore.extend(scope.statements)
        statsBefore.extendAt(statsAfter,-2)
        scope.statements = statsBefore

    def parseWhile(self,loop:WhileLoop,addContinue = True):
        stats = ArrayList()
        exitLabel = loop.node.exitLabel()
        label = loop.node.label
        continueLabel = "C"+label
        self.continueLabel.append(continueLabel)
        self.breakLabel.append(exitLabel)
        self.parseBlock(loop.node,False)
        scope = self.scopes.get(label)
        stats.append(TAC(Tnames.LABEL,label))
        if addContinue:
            stats.append(TAC(Tnames.LABEL,continueLabel))
        stats.extend(self.untangleExpression(loop.condition))
        stats.append(TAC(Tnames.JUMPZ,exitLabel,self.makeTmp(0)))
        stats.extend(scope.statements)
        stats.append(TAC(Tnames.JUMP,label))
        stats.append(TAC(Tnames.LABEL,exitLabel))
        scope.statements = stats
        #self.scopes.put(scope.label,scope)
        self.breakLabel.pop()
        self.continueLabel.pop()

    def parseIf(self,st:IfStatement):


        for i in range(0,st.condition.__len__()):
            statements = []
            notLabel = "N"+st.blocks[i].label
            self.parseBlock(st.blocks[i])
            statements.extend(self.untangleExpression(st.condition[i]))
            statements.append(TAC(Tnames.JUMPZ,notLabel,self.makeTmp(0)))

            scope = self.scopes.get(st.blocks[i].label)
            scope.statements.extendAt(statements,0)
            scope.statements.insert(-1,TAC(Tnames.JUMP,st.blocks[i].exitLabel()))
            scope.statements.insert(-1,TAC(Tnames.LABEL,notLabel))
            try:
                scope.statements.insert(-1,TAC(Tnames.CALLBLOCK,st.blocks[i+1].label))
            except Exception:
                pass

        if st.containsElse:
            self.parseBlock(st.blocks[-1])

    def untangleExpression(self,exp:AST,index=0):
        statements = []

        def untangleExp(exp:AST,index:int):
            if isinstance(exp,EXP):
                if isinstance(exp,BinaryOperator):
                    untangleExp(exp.left,index)
                    untangleExp(exp.right,index+1)
                    statements.append(self.generateArithmetic(exp.op.type,index,index+1))

                if isinstance(exp, Literall):
                    statements.append(TAC(Tnames.LOAD,self.makeTmp(index),[exp.token.type, exp.token.value]))
            if isinstance(exp,ValueCall):
                if isinstance(exp, FunctionCall):
                    if not self.nameIsDefined(self.currentBlockLabel,exp.name,function=True,checkOnlyLocal=False):
                        raise SemanticException("Function "+exp.name+" is not defined in " + self.currentBlockLabel)
                    for par in exp.parameters:
                        statements.extend(self.untangleExpression(par,index))
                        statements.append(TAC(Tnames.PUSH,self.makeTmp(index)))
                    amount = exp.parameters.__len__()
                    statements.append(TAC(Tnames.LOAD,self.makeTmp(index),[LexName.INTEGER_CONST,amount]))
                    statements.append(TAC(Tnames.PUSH,self.makeTmp(index)))
                    statements.append(TAC(Tnames.CALL,exp.name))
                    statements.append(TAC(Tnames.POP,self.makeTmp(index)))
                elif isinstance(exp, ArrayCall):
                    if not self.nameIsDefined(self.currentBlockLabel,exp.name,False):
                        raise SemanticException("Array "+exp.name+" is not defined")
                    untangleExp(exp.index,index+1)
                    statements.append(TAC(Tnames.LOADARR,self.makeTmp(index),[exp.name,self.makeTmp(index+1)]))
                else:
                    if not self.nameIsDefined(self.currentBlockLabel,exp.name,False):
                        raise SemanticException("Variable "+exp.name+" is not defined")
                    statements.append(TAC(Tnames.LOAD,self.makeTmp(index),exp.name))
            if exp.negation:
                statements.append(TAC(LexName.NOT,self.makeTmp(index)))


        untangleExp(exp,index)
        return statements

    def generateArithmetic(self,operation,reg1:int,reg2:int)->TAC:
        return TAC(operation,self.makeTmp(reg1),self.makeTmp(reg2))















