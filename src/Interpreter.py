
from definitions import *
from src.LexNames import LexName
from src.SpecificTypes import Scope, Reg, StaticArray, TVariable, Operation, TFunction

from src.TAC import TAC, Tnames
from src.lexer import Token, Lexer
from src.lib import OrderedMap, ArrayList
from src.parser import Parser




class Interpreter(object):

    builtInFunctions = ['input','print']
    @staticmethod
    def prepateAST(file):
        print("Lexer start")
        Token.readLanguageDefinition(HOME_DIR+"/src/param/reserved.txt")
        print("Lexer initialization end")
        lexer = Lexer(file)
        lexer.lexerize()
        print(lexer.tokenList)
        for token in lexer.tokenList:
            if token.type == LexName.LEXER_ERROR:
                raise LexerException(token.__str__())
        parser = Parser(lexer.tokenList)
        beforeParsing = len(parser.tokenList)
        print("Blocks left and right matching: " + str(parser.countBlocks()))
        root = parser.root()

        while parser.needReparse:
            print("Reparsing")
            parser.needReparse = False
            root = parser.root()
            print("Updated token list")
            print(parser.tokenList)

        print("Updated token list")
        print(parser.tokenList)
        if beforeParsing != parser.tokenList.__len__():
            print("Mistakes were found at:")
            for token in parser.tokenList:
                if token.value is None:
                    print(token)
            print("Before:" + str(beforeParsing) + " After: " + str(parser.tokenList.__len__()))
        else:
            print("No syntax mistakes")
        return root

    @staticmethod
    def simpleTest(file):
        root = Interpreter.prepateAST(file)
        w = open(file+".xml", "w")
        w.write(root.xml())
        return root

    def __init__(self,scopes:OrderedMap):
        self.scopes = scopes
        self.stack = ArrayList(None,None)
        self.registers = OrderedMap()
        self.currentBlock = Scope("0B")
        self.rootLabel = "0B"
        self.callStack = ArrayList(None,None)
        self.usedStackValues = ArrayList(None,None)

    def stringRegisters(self):
        string = ""
        for reg in self.registers.returnItemsInOrder():
            string += reg.__str__()+"\n"
        return string

    def setOrGetRegister(self,regName):
        scope = self.callStack.getLast()
        if scope.registers.containsKey(regName):
            return scope.registers.get(regName)
        else:
            scope.registers.put(regName,Reg(regName))
            return scope.registers.get(regName)




    def resolveType(self,t:str):
        if LexName.INT in t:
            return LexName.INT
        if LexName.FLOAT in t:
            return LexName.FLOAT
        if LexName.STRING in t:
            return LexName.STRING
        if LexName.NULL in t:
            return LexName.NULL
        if t in [LexName.TRUE,LexName.FALSE]:
            return LexName.BOOL
        return t

    def fetchValue(self,name:str)->TVariable:
        for scope in self.callStack.getItemsInReverseOrder():
            if scope.variables.containsKey(name):
                return scope.variables.get(name)
        raise SemanticException("Value "+name+" was not found")

    def fetchFunction(self,name:str)->TFunction:
        for scope in self.callStack.getItemsInReverseOrder():
            if scope.functions.containsKey(name):
                return scope.functions.get(name)
        raise SemanticException("Function "+name+" was not found")

    def generateScope(self,startingLabel)->Scope:
        return Operation.generateScope(self.scopes.get(startingLabel),"")

    def doFunction(self,startingLabel,functionName)->Scope:
        if functionName in Interpreter.builtInFunctions:
            raise Exception("Not yet")
        else:

            for scope in self.scopes.returnItemsInOrder():
                if scope.functions.containsKey(functionName):
                    fLabel = scope.functions.get(functionName).label
                    return Operation.generateScope(self.scopes.get(fLabel))
                if scope.functionName == functionName:
                    if scope.label in startingLabel:
                        return Operation.generateScope(self.scopes.get(startingLabel))
            raise Exception("Failed to call "+functionName +" from "+ startingLabel)






    def doJumpNew(self,label):
        for scope in self.callStack.getItemsInReverseOrder():
            i = 0
            if scope is None:
                raise SemanticException("No scopes found at "+label)
            for st in scope.statements:
                if st.tuple[0] == Tnames.LABEL and st.tuple[1] == label:
                    return [scope.label,i]
                i+=1
        raise SemanticException("Failed Jump")

    def doReturn(self,label=None)->int:
        if label is None:
            self.usedStackValues.append(self.callStack.pop())
            self.currentBlock = self.callStack.getLast()
        else:
            while True:
                if self.currentBlock.label == label:
                    self.usedStackValues.append(self.callStack.pop())
                    self.currentBlock = self.callStack.getLast()
                    break
                else:
                    self.usedStackValues.append(self.callStack.pop())
                    self.currentBlock = self.callStack.getLast()
                if self.currentBlock is None:
                    print("End reached")
                    return -1

        if self.currentBlock is None:
            print("End reached")
            return -1

        print("Call stack:" + str(self.callStack))
        return self.currentBlock.returnIndex


    def interpretBlockNew(self, label: str):
        self.callStack.append(self.generateScope(label))
        self.currentBlock = self.callStack.getLast()
        print("Call stack:" + str(self.callStack))
        i = -1
        while True:
            i += 1
            if i >= self.currentBlock.statements.__len__():
                # return after CALLBLOCK/CALL to previous spot
                i = self.doReturn()
                if i == -1:
                    break
            #pre-evaluation

            st = self.currentBlock.statements[i]
            string = ""
            for reg in self.currentBlock.registers.returnItemsInOrder():
                string+=str(reg)
            print(str(i).zfill(3)+":",st,string)
            operation = st.operation
            if operation == Tnames.LABEL:
                pass
            elif operation == Tnames.CALLBLOCK:
                # self.currentBlock.returnIndex = i
                self.currentBlock.returnIndex = i
                scope = Operation.generateScope(self.scopes.get(st.tuple[1]))
                self.currentBlock = scope
                self.callStack.append(scope)
                print("Call stack:"+str(self.callStack))
                i = -1
            elif operation == Tnames.JUMP:
                tup = self.doJumpNew(st.tuple[1])
                self.currentBlock = self.scopes.get(tup[0])
                i = tup[1]


            elif operation == Tnames.JUMPZ:
                reg = self.setOrGetRegister(st.tuple[1])
                if not reg.booleanValue():
                    tup = self.doJumpNew(st.tuple[2])
                    self.currentBlock = self.scopes.get(tup[0])
                    i = tup[1]

            elif operation == Tnames.CALL:
                # reg = self.setOrGetRegister("_temp")
                self.currentBlock.returnIndex = i
                self.evaluate(TAC(Tnames.POP,"_temp"))
                reg = self.setOrGetRegister("_temp")
                if reg.value != self.fetchFunction(st.tuple[1]).parameters.__len__():
                    raise SemanticException("Function Parameter amount miss-match")

                func = self.doFunction(self.callStack.getLast(),st.tuple[1])
                self.currentBlock = func
                self.callStack.append(func)
                print("Call stack:" + str(self.callStack))
                i = -1
            elif operation == Tnames.RETURN:
                fetched = self.fetchFunction(st.tuple[2])
                val = self.stack.getLast()
                if val.tp() != fetched.tp():
                    if val.tp() == LexName.NULL:
                        raise SemanticException("Function " + st.tuple[2] + " " + "returned nothing")
                    raise SemanticException("Function "+st.tuple[2]+" "+"returned different type than declared")
                i = self.doReturn(st.tuple[1])
                if i == -1:
                    break
            else:
                #Non block jumping command
                self.evaluate(st)



    def evaluate(self,st:TAC):
        '''Black hole "all in one method" for ALL Statements'''
        if st.operation == Tnames.LOAD:
            value = st.tuple[2]
            reg = self.setOrGetRegister(st.tuple[1])
            #resolve if its const or not
            if isinstance(value,list):
                t = self.resolveType(value[0])
                reg.t = t
                # its a simple const value
                if t == LexName.NULL:
                    reg.value = None
                elif t == LexName.BOOL:
                    reg.value = value[0] == LexName.TRUE
                else:
                    reg.value = value[1]
            elif "_" in value:
                # Register call
                reg1 = self.setOrGetRegister(value)
                reg.t = reg1.t
                reg.value = reg1.value
            else:
                #value fetch
                varName = st.tuple[2]
                var = self.fetchValue(varName)
                regName = st.tuple[1]
                reg = self.setOrGetRegister(regName)
                reg.t = var.t
                reg.value = var.value

        elif st.operation == Tnames.INIT:
            name = st.tuple[1][1] #get the name
            regName = st.tuple[2]
            reg = self.setOrGetRegister(regName)
            var = self.currentBlock.variables.get(name)
            var.value = reg.value
            if reg.t == LexName.NULL:
                var.value = None
            elif (var.tp() != reg.tp()) and (reg.tp() is not None):
                raise SemanticException("Type miss match")
            else:
                var.t = reg.t
        elif st.operation == Tnames.INITARR:
            regName = st.tuple[1]
            reg = self.setOrGetRegister(regName)
            name = st.tuple[2][1]
            t = st.tuple[2][0]
            var = self.currentBlock.variables.get(name)
            if reg.tp() != LexName.INT:
                raise SemanticException("Array size must be INT")
            var.value = StaticArray(reg.value,t)
        elif st.operation == Tnames.LOADARR:
            # Load from Array
            regName = st.tuple[1]
            reg = self.registers.get(regName)
            indexRegName = st.tuple[2][1]
            indexReg = self.setOrGetRegister(indexRegName)
            arrayName = st.tuple[2][0]
            array = self.fetchValue(arrayName)
            if indexReg.tp() != LexName.INT:
                raise SemanticException("Array index must be INT")
            else:
                reg.value = array.value[indexReg.value].value
                reg.t = array.t

        elif st.operation == Tnames.PUSH:
            regName = st.tuple[1]
            reg = self.setOrGetRegister(regName)
            self.stack.append(reg.toTVariable())

        elif st.operation == Tnames.POP:
            regName = st.tuple[1]
            reg = self.setOrGetRegister(regName)
            val = self.stack.pop()
            reg.t = val.t
            reg.value = val.value

        elif st.operation == LexName.NOT:
            regName = st.tuple[1]
            reg = self.setOrGetRegister(regName)
            booleanValue = reg.booleanValue()
            if reg.tp() == LexName.BOOL:
                reg.value = not booleanValue
            else:
                raise SemanticException("Can't invert non-boolean value")
        elif st.operation in LexName.Operators:
            operation = st.operation
            op1 = st.tuple[1]
            op2 = st.tuple[2]
            src = self.setOrGetRegister(op2)
            dest = None
            if isinstance(op1,list):
            # TODO operation with arrays
                indexReg = self.setOrGetRegister(op1[1])
                if indexReg.tp() != LexName.INT:
                    raise SemanticException("Array index is not INT")
                arrayName = op1[0]
                array = self.fetchValue(arrayName).value
                dest = array[indexReg.value]
            else:
                name = op1
                if "_" in name:
                    dest = self.setOrGetRegister(name)
                else:
                    dest = self.fetchValue(name)
            if not Operation.operationDefined(operation,dest.tp(),src.tp()):
                raise SemanticException(operation+" is not defined to "+dest.tp() + " "+src.tp())
            if operation == LexName.ASSIGN:
                if src.value is None:
                    dest.value = None
                elif src.tp() == LexName.INT and dest.tp() == LexName.FLOAT:
                    dest.value = float(src.value)
                else:
                    dest.value = src.value
            else:
                if (operation in LexName.LogicOperators) or (operation in LexName.CompareOperators):
                    dest.t = LexName.BOOL
                    if operation == LexName.EQUALS:
                        dest.value = dest.value == src.value
                    elif operation == LexName.NOTEQUAL:
                        dest.value = dest.value != src.value
                    elif operation == LexName.GREATER:
                        dest.value = dest.value > src.value
                    elif operation == LexName.GREATEREQUAL:
                        dest.value = dest.value >= src.value
                    elif operation == LexName.LESS:
                        dest.value = dest.value < src.value
                    elif operation == LexName.LESSEQUAL:
                        dest.value = dest.value >= src.value
                    elif operation == LexName.AND:
                        dest.value = dest.booleanValue() and src.booleanValue()
                    elif operation == LexName.OR:
                        dest.value == dest.booleanValue() or src.booleanValue()

                elif operation in [LexName.PLUS,LexName.MINUS,LexName.MULTIPLY,LexName.DIVIDE] or operation in LexName.AdvancedAssign:
                    typePromote = False
                    if src.tp() == LexName.INT and dest.tp() == LexName.FLOAT:
                        typePromote = True
                    if operation in [LexName.PLUS,LexName.ASSIGNPLUS]:
                        dest.value = dest.value + src.value
                    elif operation in [LexName.MINUS,LexName.ASSIGNMINUS]:
                        dest.value = dest.value - src.value
                    elif operation in [LexName.MULTIPLY,LexName.ASSIGNMULTIPLY]:
                        dest.value = dest.value * src.value
                    elif operation in [LexName.DIVIDE,LexName.ASSIGNDIVIDE]:
                        if dest.t == LexName.FLOAT:
                            dest.value = dest.value / src.value
                        else:
                            dest.value = dest.value // src.value





# def main():
#     while True:
#         try:
#             text = input('calc> ')
#         except EOFError:
#             break
#         if not text:
#             continue
#         interpreter = Interpreter(text)
#         result = interpreter.expr()
#         print(result)
