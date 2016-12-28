import datetime

from definitions import *
from src.ASTnodes import FnParameter, Block
from src.LexNames import LexName
from src.Optimizer import Optimizer
from src.SpecificTypes import Scope, Reg, StaticArray, TVariable, Operation, TFunction

from src.TAC import TAC, Tnames, TACgen
from src.lexer import Token, Lexer
from src.lib import OrderedMap, ArrayList, eprint
from src.parser import Parser





class Interpreter:
    @staticmethod
    def prepateAST(file,debug=False):
        if debug:
            print("Lexer start")
        Token.readLanguageDefinition(HOME_DIR+"/src/param/reserved.txt")
        if debug:
            print("Lexer initialization end")
        lexer = Lexer(file)
        lexer.lexerize()
        if debug:
            print(lexer.tokenList)
        for token in lexer.tokenList:
            if token.type == LexName.LEXER_ERROR:
                raise LexerException(token.__str__())
        parser = Parser(lexer.tokenList)
        beforeParsing = len(parser.tokenList)
        if debug:
            print("Blocks left and right matching: " + str(parser.countBlocks()))
        root = parser.root()

        while parser.needReparse:
            if debug:
                print("Reparsing")
            parser.needReparse = False
            root = parser.root()
        if debug:
            print("Updated token list")
            print(parser.tokenList)

        for token in parser.tokenList:
            if token.value is None:
                parser.mistakesFoundAt.append(token)
        if parser.mistakesFoundAt.__len__()>0:
            print("Before:" + str(beforeParsing) + " After: " + str(parser.tokenList.__len__()))
            print("Mistakes were found at:")
            for mistake in parser.mistakesFoundAt:
                print(mistake)
        else:
            print("No syntax mistakes")
        return root

    @staticmethod
    def prepareTACgen(root:Block)->TACgen:
        t = TACgen()
        Interpreter.addDefaultGlobalFunctions(t)
        t.parseRoot(root)
        return t

    @staticmethod
    def optimizeTest(file,debug=False):
        root = Interpreter.prepateAST(file)
        t = Interpreter.prepareTACgen(root)
        for st in t.getStatementsAsString():
            print(st)
        Optimizer.output = debug
        print("\nOptimize!\n")
        Optimizer.scopes = t.scopes
        t = Optimizer.optimize(t)
        print("\nAfter:\n")

        for st in t.getStatementsAsString():
            print(st)

    @staticmethod
    def simpleTest(file,debug=False,optimize=True)->list:

        root = Interpreter.prepateAST(file)
        t = Interpreter.prepareTACgen(root)
        if debug:
            for s in t.getStatementsAsString():
                print(s)

        Optimizer.output = debug
        if optimize:
            t = Optimizer.optimize(t)
        else:
            Optimizer.scopes = t.scopes
            for scope in t.scopes.returnItemsInOrder():
                Optimizer.removeTags(scope)
        if debug:
            print("AFTER:")
            for s in t.getStatementsAsString():
                print(s)

        i = Interpreter(t.scopes)
        i.debug = debug
        i.globalFunctions = t.globalFunctions
        dateStart = datetime.datetime.now()
        if t.scopes.containsKey(t.rootLabel):
            i.interpretBlock(t.rootLabel)
        dateEnd = datetime.datetime.now()
        return [dateStart,dateEnd,dateEnd-dateStart]



    @staticmethod
    def addDefaultGlobalFunctions(t:TACgen):
        def f1(ob: list):
            eprint(ob[0])
            return [LexName.NULL, ""]

        def f2(ob: list):
            string = input()
            return [LexName.STRING, string]

        def f3(ob: list):
            return [LexName.STRING, str(ob[0])]

        def f4(ob: list):
            string = ob[0]
            try:
                i = int(string)
            except ValueError:
                i = 0
            return [LexName.INT, i]

        def f5(ob: list):
            string = ob[0]
            index = ob[1]
            try:
                char = string[index]
            except Exception:
                char = None
            return [LexName.STRING, char]

        t.addGlobalFunction(TFunction([LexName.NULL, False], Token.get(LexName.PRINT),"Global",
                                      [FnParameter(LexName.STRING, "ob")], f1))
        t.addGlobalFunction(TFunction([LexName.STRING, False], Token.get(LexName.INPUT),"Global",
                                      [], f2))
        t.addGlobalFunction(TFunction([LexName.STRING, False], "toStr", "Global",
                                      [FnParameter(LexName.STRING, "ob")], f3))
        t.addGlobalFunction(TFunction([LexName.INT, False], "toInt", "Global",
                                      [FnParameter(LexName.STRING, "ob")], f4))
        t.addGlobalFunction(TFunction([LexName.STRING, False], "charAt", "Global",
                                      [FnParameter(LexName.STRING, "ob"), FnParameter(LexName.INT, "i")], f5))

    def __init__(self,scopes:OrderedMap):
        self.scopes = scopes
        self.stack = ArrayList(None,None)
        self.currentBlock = Scope("0B")
        self.rootLabel = "0B"
        self.callStack = ArrayList(None,None)
        self.usedStackValues = ArrayList(None,None)
        self.globalFunctions = OrderedMap()
        self.executedStatements = ArrayList(None,None)
        self.debug = False

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
        if self.globalFunctions.containsKey(name):
            return self.globalFunctions.get(name)
        for scope in self.callStack.getItemsInReverseOrder():
            if scope.functions.containsKey(name):
                return scope.functions.get(name)
        raise SemanticException("Function "+name+" was not found")

    def generateScope(self,startingLabel)->Scope:
        return Operation.generateScope(self.scopes.get(startingLabel),"")

    def doFunction(self,startingLabel,functionName)->Scope:
        for scope in self.scopes.returnItemsInOrder():
            if scope.functions.containsKey(functionName):
                fLabel = scope.functions.get(functionName).label
                return Operation.generateScope(self.scopes.get(fLabel))
            if scope.functionName == functionName:
                if scope.label in startingLabel:
                    return Operation.generateScope(self.scopes.get(startingLabel))
        raise Exception("Failed to call "+functionName +" from "+ startingLabel)

    def doJump(self, label):
        for scope in self.callStack.getItemsInReverseOrder():
            if scope is None:
                raise SemanticException("No scopes found at "+label)
            i = 0
            for st in scope.statements:

                if st.tuple[0] == Tnames.LABEL and st.tuple[1] == label:
                    self.currentBlock = scope
                    return i
                i += 1
        raise SemanticException("Failed Jump")

    def doReturn(self,label=None)->int:
        if label is None:
            label = self.currentBlock.label
            self.currentBlock = self.callStack.getLast()
        while True:
            if self.currentBlock.label == label:
                self.usedStackValues.append(self.callStack.pop())
                self.currentBlock = self.callStack.getLast()
                break
            else:
                self.usedStackValues.append(self.callStack.pop())
                self.currentBlock = self.callStack.getLast()
            if self.currentBlock is None:
                self.executedStatements.append("End reached")
                if self.debug:
                    print(self.executedStatements.getLast())
                return -1

        if self.currentBlock is None:
            self.executedStatements.append("End reached")
            if self.debug:
                print(self.executedStatements.getLast())
            return -1

        self.executedStatements.append("Call stack:" + str(self.callStack))
        if self.debug:
            print(self.executedStatements.getLast())
        return self.currentBlock.returnIndex

    def interpretBlock(self, label: str):
        self.callStack.append(self.generateScope(label))
        self.currentBlock = self.callStack.getLast()
        self.executedStatements.append("Call stack:" + str(self.callStack))
        if self.debug:
            print(self.executedStatements.getLast())
        i = -1
        while True:
            i += 1
            if i >= self.currentBlock.statements.__len__():
                # return after CALLBLOCK/CALL to previous spot
                i = self.doReturn()
                if i == -1:
                    break
                i+=1
            # pre-evaluation
            if i >= self.currentBlock.statements.__len__():
                break
            try:
                # found end
                st = self.currentBlock.statements[i]
            except IndexError as e:
                print(e,"at",i)

                break
            string = ""
            for reg in self.currentBlock.registers.returnItemsInOrder():
                string+=str(reg)
            self.executedStatements.append(str(i).zfill(3)+":"+str(st)+string)
            if self.debug:
                print(self.executedStatements.getLast())
            operation = st.operation
            if operation in [Tnames.CALLBLOCK,Tnames.CALL]:
                scope = None
                if operation == Tnames.CALL:
                    argumentCount = self.stack.pop().value
                    fetched = self.fetchFunction(st.tuple[1])
                    if argumentCount != fetched.parameters.__len__():
                        raise SemanticException("Function Parameter amount miss-match")
                    # global function
                    if self.globalFunctions.containsKey(fetched.name):
                        variables = []
                        for var in range(0,fetched.parameters.__len__()):
                            variables.insert(0,self.stack.pop().value)
                        retVal = fetched.execute(variables)
                        systemReg = Reg("_sysReg")
                        systemReg.t = retVal[0]         # set type
                        systemReg.value = retVal[1]     # set value
                        self.stack.append(systemReg)
                    else:
                        scope = self.doFunction(self.callStack.getLast(), st.tuple[1])
                else:
                    scope = Operation.generateScope(self.scopes.get(st.tuple[1]))
                if scope is not None:
                    self.currentBlock.returnIndex = i
                    self.callStack.append(scope)
                    self.currentBlock = self.callStack.getLast()
                    self.executedStatements.append("Call stack:"+str(self.callStack))
                    if self.debug:
                        print(self.executedStatements.getLast())
                    i = -1
            elif operation in [Tnames.JUMPZ,Tnames.JUMP]:
                boolVal = True
                if operation == Tnames.JUMPZ:
                    reg = self.setOrGetRegister(st.tuple[2])
                    boolVal = reg.booleanValue()
                if (operation==Tnames.JUMP) or (not boolVal):
                    index = self.doJump(st.tuple[1])
                    i = index

            elif operation == Tnames.RETURN:
                fetched = self.fetchFunction(st.tuple[2])
                val = self.stack.getLast()
                if val.tp() != fetched.tp():
                    if val.tp() == LexName.NULL:
                        raise SemanticException("Function " + st.tuple[2] + " " + "returned nothing")
                    raise SemanticException("Function "+st.tuple[2]+" "+"returned different "+val.tp()+" declared"+fetched.tp())
                i = self.doReturn(st.tuple[1])
                if i == -1:
                    break
            else:
                #Non block jumping command
                self.evaluate(st)

    def evaluate(self,st:TAC):
        """Black hole all in one method" for ALL Statements"""
        if st.operation == Tnames.LOAD:
            value = st.tuple[2]
            reg = self.setOrGetRegister(st.tuple[1])
            # resolve if its const or not
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
                # value fetch
                varName = st.tuple[2]
                var = self.fetchValue(varName)
                regName = st.tuple[1]
                reg = self.setOrGetRegister(regName)
                reg.t = var.t
                reg.value = var.value

        elif st.operation == Tnames.INIT:
            name = st.tuple[1][1] # get the name
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
            regName = st.tuple[2]
            reg = self.setOrGetRegister(regName)
            name = st.tuple[1][1]
            t = st.tuple[1][0]
            var = self.currentBlock.variables.get(name)
            if reg.tp() != LexName.INT:
                raise SemanticException("Array size must be INT")
            var.value = StaticArray(reg.value,t)
        elif st.operation == Tnames.LOADARR:
            # Load from Array
            regName = st.tuple[1]
            reg = self.setOrGetRegister(regName)
            indexRegName = st.tuple[2][1]
            indexReg = self.setOrGetRegister(indexRegName)
            arrayName = st.tuple[2][0]
            array = self.fetchValue(arrayName)
            reg.value = array.value.get(indexReg).value
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
