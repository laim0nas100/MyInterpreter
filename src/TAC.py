from src.ASTnodes import *
from src.LexNames import LexName
from src.lib import ArrayList


class Tnames:
    LOAD = "LOAD" #loads to register following value
    JUMP = "JUMP"
    JUMPZ = "JUMPZ" #jump if operand is zero to label {x, label}
    LOADARR = "LOADARR" #loads to register x from array[x]
    LABEL = "LABEL" #creates new label
    INIT = "INIT" #initialises new variable {name, value}
    INITARR = "INITARR" #initialises new array {size, [type,name]}


class TAC:
    def __init__(self,operation,operand0,operand1=None):
        if operand1 is None:
            self.tuple = [operation, operand0]
        else:
            self.tuple = [operation,operand0,operand1]

    def __str__(self):
        s = ""
        for t in self.tuple:
            s += " "+t.__str__()
        return s+";"

class Scope:
    def __init__(self,number,parents=None):
        self.number = number
        self.children = ArrayList(None,None)
        self.parents = ArrayList(None,None)
        self.statements = ArrayList(None,None)
        if parents is not None:
            for par in parents:
                self.addParent(par)

    def addChild(self,number):
        self.children.append(number)

    def addParent(self,number):
        self.parents.append(number)

def makeTmp(index:int):
    return "_t"+str(index)

class TACgen:
    def __init__(self):
        self.scopes = dict()
        # create root scope
        self.rootScope = Scope(0)
        self.scopes.setdefault("_0",self.rootScope)

    def addRelation(self,parentScope:Scope,childScope:Scope):
        parentScope.addChild(childScope.number)
        childScope.addParent(parentScope.number)




    def parseBlock(self,block:Block):
        statements = list()
        if isinstance(block,Block):
            statements.append(self.generateLabel(block.label))
            for st in block.statements:
                statements.extend(self.parseStatement(st))
        return statements

    def parseStatement(self,statement:Statement):
        statements = list()

        if isinstance(statement,Statement):
            node = statement.node

            if isinstance(node,VariableAssign):
                statements.extend(self.untangleExpression(node.value))
                statements.append(self.generateLoad(node.name,makeTmp(0)))
            elif isinstance(node,VariableDeclaration):
                if isinstance(node,VariableInitialization):
                    statements.extend(self.untangleExpression(node.value))
                    statements.append(self.generateInit(node.name,makeTmp(0)))
                elif isinstance(node,ArrayDeclaration):
                    statements.extend(self.untangleExpression(node.size))
                    statements.append(self.generateInitArr(makeTmp(0),[node.type,node.name]))
                else:
                    statements.append(self.generateInit(node.name, Null(Token(LexName.NULL,None))))
            elif isinstance(node, WhileLoop):
                if isinstance(node, ForLoop):
                    pass
                else:
                    statements.extend(self.parseWhile(node))

            elif isinstance(node,Block):
                #TODO: manage scope jumps
                statements.extend(self.parseBlock(node))
        return statements


    def parseWhile(self,loop:WhileLoop):
        statements = list()
        exitLabel = "E"+loop.node.label
        repeatLabel = loop.node.label
        statements.append(self.generateLabel(repeatLabel))
        statements.extend(self.untangleExpression(loop.condition))
        statements.append(self.generateJumpZ(makeTmp(0),exitLabel))
        statements.extend(self.parseStatement(loop.node))
        statements.append(self.generateJump(repeatLabel))
        statements.append(self.generateLabel(exitLabel))
        return statements

    def untangleExpression(self,exp:AST):
        statements = []

        def untangleExp(index:int,exp:AST):
            if isinstance(exp,BinaryOperator):
                untangleExp(index,exp.left)
                untangleExp(index+1,exp.right)
                statements.append(self.generateArithmetic(exp.op.type,index,index+1))

            if isinstance(exp, Literall):
                statements.append(self.generateLoad(makeTmp(index),[exp.token.type, exp.token.value]))
            if isinstance(exp,ValueCall):
                if isinstance(exp, FunctionCall):
                    pass
                    # toBeImplemented
                elif isinstance(exp, ArrayCall):
                    untangleExp(index, exp.index)
                    statements.append(self.generateLoadArray(makeTmp(index),exp.name))
                else:
                    statements.append(self.generateLoad(makeTmp(index),exp.name))



        untangleExp(0,exp)
        return statements

    def generateInit(self,dest,src):
        return TAC(Tnames.INIT, dest, src)

    def generateInitArr(self,dest,typeAndSize:list):
        return TAC(Tnames.INITARR,dest,typeAndSize)

    def generateArithmetic(self,operation,reg1:int,reg2:int):
        return TAC(operation,makeTmp(reg1),makeTmp(reg2))

    def generateLoad(self,dest,src):
        return TAC(Tnames.LOAD,dest,src)

    def generateLoadArray(self,dest,src):
        return TAC(Tnames.LOADARR,dest,src)

    def generateLabel(self,name):
        return TAC(Tnames.LABEL,name)

    def generateJumpZ(self,oper,label):
        return TAC(Tnames.JUMPZ,oper,label)

    def generateJump(self,label):
        return TAC(Tnames.JUMP,label)










