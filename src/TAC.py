from src.ASTnodes import *
from src.LexNames import LexName
from src.lib import ArrayList, OrderedMap



class SemanticException(Exception):
    pass
class Tnames:
    LOAD = "LOAD" #loads to register following value
    JUMP = "JUMP" #jumps within all scopes
    JUMPBLOCK = "JUMPBLOCK" #jumps within scope
    JUMPZ = "JUMPZ" #jump if operand is zero to label {x, label}
    LOADARR = "LOADARR" #loads to register x from [array, index]
    LABEL = "LABEL" #creates new label
    INIT = "INIT" #initialises new variable {type,value,name}
    INITARR = "INITARR" #initialises new array {size, [type,name]}
    CALLBLOCK = "CALLBLOCK" #jumps to block
    POP = "POP" #pops to register following value
    PUSH = "PUSH" #pushes to register the following value
    RETURN = "RETURN"
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

class Scope:
    def __init__(self,label):
        self.label = label
        self.statements = ArrayList(None,None)
        self.variables = OrderedMap()
        self.functions = OrderedMap()
        self.functionName = None

    def getExitLabel(self):
        return "E"+self.label

class Type:
    i = "int"
    f = "float"
    s = "string"
    b = "boolean"
    types = [i,f,s,b]

    def __init__(self,t,isArray=False):
        self.isArray = isArray
        if t in Type.types:
            self.t = t
        else:
            raise SemanticException("type missmatch")

class Variable:

    def __init__(self,t:Type,name):
        self.tp = t
        self.name = name

class Function(Variable):
    def __init__(self,t:Type,name):
        super().__init__(t,name)


class Register:
    def __init__(self):
        self.name = None
        self.type = None
        self.value = None

def makeTmp(index:int):
    return "_t"+str(index)

class TACgen:
    def __init__(self):
        self.scopes = OrderedMap()
        self.currentBlockLabel = None
        self.currentBlock = None
        self.continueLabel = None
        self.breakLabel = None
        self.functionReturnTo = None
        self.rootLabel = "0B"
        self.registerStack = ArrayList(None,None)

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


    def parseBlock(self,block:Block,putLabel=True):
        scope = Scope(block.label)
        if self.scopes.containsKey(block.label):
            scope = self.scopes.get(scope.label)
        else:
            self.scopes.put(scope.label,scope)
        if putLabel:
            scope.statements.append(self.generateLabel(scope.label))
        for st in block.statements:
            self.currentBlockLabel = scope.label
            scope.statements.extend(self.parseStatement(st))
        if putLabel:
            scope.statements.append(self.generateLabel(block.exitLabel()))
        self.scopes.put(scope.label, scope)

    def parseStatement(self,statement:Statement):
        statements = list()

        if isinstance(statement,Statement):
            node = statement.node

            if isinstance(node,VariableAssign):
                if isinstance(node,ArrayElementAssign):
                    statements.extend(self.parseArrayElementAssign(node))
                else:
                    statements.extend(self.untangleExpression(node.value))
                    statements.append(TAC(node.operator.type,node.name,makeTmp(0)))
            elif isinstance(node,VariableDeclaration):
                if isinstance(node,VariableInitialization):
                    statements.extend(self.untangleExpression(node.value))
                    statements.append(self.generateInit(node,makeTmp(0)))
                elif isinstance(node,ArrayDeclaration):
                    statements.extend(self.untangleExpression(node.size))
                    statements.append(self.generateInitArr(makeTmp(0),[node.type,node.name]))
                elif isinstance(node,FunctionDeclaration):
                    self.parseDefineFunction(node)

                else:
                    statements.append(self.generateInit(node.name, Null(Token(LexName.NULL,None))))
            elif isinstance(node, WhileLoop):
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
                statements.append(TAC(Tnames.PUSH,makeTmp(0)))
                statements.append(TAC(Tnames.RETURN,self.currentBlockLabel))
            elif isinstance(node,BreakStatement):
                if self.breakLabel is not None:
                    statements.append(TAC(Tnames.JUMP,self.breakLabel))
            elif isinstance(node,ContinueStatement):
                if self.continueLabel is not None:
                    statements.append(TAC(Tnames.JUMP,self.continueLabel))
            elif isinstance(node,IfStatement):
                statements.append(TAC(Tnames.CALLBLOCK,node.blocks[0].label))
                self.parseIf(node)
            elif isinstance(node,EXP):
                statements.extend(self.untangleExpression(node))
        return statements



    def parseDefineFunction(self,node:FunctionDeclaration):
        self.parseBlock(node.body)
        functionScope = self.scopes.get(node.body.label)
        functionScope.functionName = node.name
        #popping variables from stack
        for p in node.parameters:


            functionScope.statements.insert(1,TAC("POP", makeTmp(0)))
            functionScope.statements.insert(2, TAC(Tnames.LOAD, p.name, makeTmp(0)))

        # f.functions.append([node.type,node.isArray,node.name])


    def parseArrayElementAssign(self,node:ArrayElementAssign):
        statements = []
        statements.extend(self.untangleExpression(node.value))
        statements.append(TAC(Tnames.PUSH, makeTmp(0)))
        #_t1 = index, _t0 = value
        statements.extend(self.untangleExpression(node.index))
        statements.append(self.generateLoad(makeTmp(1),makeTmp(0)))
        statements.append(TAC(Tnames.POP,makeTmp(0)))
        statements.append(TAC(node.operator.type,[node.name,makeTmp(1)],makeTmp(0)))
        return statements


    def parseFor(self,loop:ForLoop):
        label = loop.node.label
        self.parseWhile(loop,False)
        scope = self.scopes.get(label)
        scope.statements.insert(0,TAC(Tnames.LABEL,"C"+scope.label))
        scope.statements.extendAt(self.parseStatement(loop.var), 0)
        scope.statements.extendAt(self.parseStatement(loop.incrementStatement),scope.statements.__len__()-2)


    def parseWhile(self,loop:WhileLoop,addContinue = True):
        stats = ArrayList()
        exitLabel = loop.node.exitLabel()
        label = loop.node.label
        continueLabel = "C"+label
        self.continueLabel = continueLabel
        self.breakLabel = exitLabel
        self.parseBlock(loop.node,False)
        scope = self.scopes.get(label)
        stats.append(self.generateLabel(label))
        if addContinue:
            stats.append(TAC(Tnames.LABEL,continueLabel))
        stats.extend(self.untangleExpression(loop.condition))
        stats.append(self.generateJumpZ(makeTmp(0),exitLabel))
        stats.extend(scope.statements)
        stats.append(TAC(Tnames.JUMPBLOCK,label))
        stats.append(self.generateLabel(exitLabel))
        scope.statements = stats
        self.scopes.put(scope.label,scope)
        self.breakLabel = None
        self.continueLabel = None

    def parseIf(self,st:IfStatement):


        for i in range(0,st.condition.__len__()):
            statements = []
            notLabel = st.blocks[i].exitLabel()
            self.parseBlock(st.blocks[i])
            statements.extend(self.untangleExpression(st.condition[i]))
            statements.append(TAC(Tnames.JUMPZ,makeTmp(0),notLabel))

            scope = self.scopes.get(st.blocks[i].label)
            scope.statements.extendAt(statements,0)
            try:
                scope.statements.append(TAC(Tnames.CALLBLOCK,st.blocks[i+1].label))
            except Exception:
                pass

        if st.containsElse:
            self.parseBlock(st.blocks[-1])


    def untangleExpression(self,exp:AST,index=0):
        statements = []

        def untangleExp(exp:AST,index:int):
            if isinstance(exp,BinaryOperator):
                untangleExp(exp.left,index)
                untangleExp(exp.right,index+1)
                statements.append(self.generateArithmetic(exp.op.type,index,index+1))

            if isinstance(exp, Literall):
                statements.append(self.generateLoad(makeTmp(index),[exp.token.type, exp.token.value]))
            if isinstance(exp,ValueCall):
                if isinstance(exp, FunctionCall):
                    for par in exp.parameters:
                        statements.extend(self.untangleExpression(par,index))
                        statements.append(TAC(Tnames.PUSH,makeTmp(index)))
                    statements.append(TAC(Tnames.CALL,exp.name))
                    statements.append(TAC(Tnames.POP,makeTmp(index)))
                elif isinstance(exp, ArrayCall):
                    untangleExp(exp.index,index+1)
                    statements.append(TAC(Tnames.LOADARR,makeTmp(index),[exp.name,makeTmp(index+1)]))
                else:
                    statements.append(self.generateLoad(makeTmp(index),exp.name))

        untangleExp(exp,index)
        return statements

    def generateInit(self,dest:VariableDeclaration,src)->TAC:
        return TAC(Tnames.INIT, [dest.type,dest.name], src)

    def generateInitArr(self,dest,typeAndSize:list)->TAC:
        return TAC(Tnames.INITARR,dest,typeAndSize)

    def generateArithmetic(self,operation,reg1:int,reg2:int)->TAC:
        return TAC(operation,makeTmp(reg1),makeTmp(reg2))

    def generateLoad(self,dest,src)->TAC:
        return TAC(Tnames.LOAD,dest,src)

    def generateLoadArray(self,dest,src:ArrayCall)->TAC:
        return TAC(Tnames.LOADARR,dest,src.name)

    def generateLabel(self,name)->TAC:
        return TAC(Tnames.LABEL,name)

    def generateJumpZ(self,oper,label)->TAC:
        return TAC(Tnames.JUMPZ,oper,label)

    def generateJump(self,label)->TAC:
        return TAC(Tnames.JUMP,label)











