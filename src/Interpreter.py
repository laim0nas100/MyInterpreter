
from definitions import *
from src.LexNames import LexName
from src.SpecificTypes import Scope, Reg, StaticArray, TVariable, Operation

from src.TAC import TAC, Tnames
from src.lexer import Token, Lexer
from src.lib import OrderedMap, ArrayList
from src.parser import Parser




class Interpreter(object):


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
        self.lastBlock = Scope("0B")
        self.rootLabel = "0B"

    def stringRegisters(self):
        string = ""
        for reg in self.registers.returnItemsInOrder():
            string += reg.__str__()+"\n"
        return string

    def setOrGetRegister(self,regName):
        if self.registers.containsKey(regName):
            return self.registers.get(regName)
        else:
            self.registers.put(regName,Reg(regName))
            return self.registers.get(regName)



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

    def fetchValue(self,scope:Scope,name:str)->TVariable:
        if scope.variables.containsKey(name):
            return scope.variables.get(name)
        else:
            return self.fetchValue(self.scopes.get(scope.getParentLabel()),name)


    def doJump(self,label):
        for block in self.scopes.returnItemsInOrder():
            i = 0
            for st in block.statements:
                if st.tuple[0] == Tnames.LABEL and st.tuple[1] == label:
                    return [block.label,i]
                i+=1
        raise SemanticException("Failed Jump")

    def interpretBlock(self, label: str):
        self.currentBlock = self.scopes.get(label)


        i = 0
        while True:
            try:
                if i >= self.currentBlock.statements.__len__()-1:
                    try:
                        #return after CALLBLOCK to previous spot
                        parentLabel = self.currentBlock.getParentLabel()
                        prevCalledBlock = self.currentBlock.label
                        self.currentBlock = self.scopes.get(parentLabel)
                        j = 0
                        for st in self.currentBlock.statements:
                            j += 1
                            if st.operation==Tnames.CALLBLOCK:
                                if st.tuple[1] == prevCalledBlock:
                                    i = j
                                    break

                    except AttributeError:
                        return
            except Exception:
                break
            #pre-evaluation
            st = self.currentBlock.statements[i]
            operation = st.operation
            if operation == Tnames.LABEL:
                pass
            elif operation == Tnames.CALLBLOCK:
                self.currentBlock = self.scopes.get(st.tuple[1])
                i = -1
            elif operation == Tnames.JUMP:
                tup = self.doJump(st.tuple[1])
                self.currentBlock = self.scopes.get(tup[0])
                i = tup[1]


            elif operation == Tnames.JUMPZ:
                reg = self.registers.get("_t0")
                if not reg.booleanValue():
                    tup = self.doJump(st.tuple[2])
                    self.currentBlock = self.scopes.get(tup[0])
                    i = tup[1]

            elif st.operation in Tnames.CALL:
                functionName = st.tuple[1]


            else:
                self.evaluate(st)
            i+=1


    def evaluate(self,st:TAC):
        '''Black hole all in one method for ALL Statements'''
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
            elif "_t" in value:
                # Register call
                reg1 = self.registers.get(value)
                reg.t = reg1.t
                reg.value = reg1.value
            else:
                #value fetch
                varName = st.tuple[2]
                var = self.fetchValue(self.currentBlock,varName)
                regName = st.tuple[1]
                reg = self.registers.get(regName)
                reg.t = var.tp()
                reg.value = var.value

        elif st.operation == Tnames.INIT:
            name = st.tuple[1][1] #get the name
            regName = st.tuple[2]
            reg = self.registers.get(regName)
            var = self.currentBlock.variables.get(name)
            var.value = reg.value
            if reg.t == LexName.NULL:
                var.value = None
            elif var.t != reg.t and reg.t:
                raise SemanticException("Type miss match")
            else:
                var.t = reg.t
        elif st.operation == Tnames.INITARR:
            regName = st.tuple[1]
            reg = self.registers.get(regName)
            name = st.tuple[2][1]
            t = st.tuple[2][0]
            var = self.currentBlock.variables.get(name)
            if reg.t != LexName.INT:
                raise SemanticException("Array size must be INT")
            var.value = StaticArray(reg.value,t)

        elif st.operation == Tnames.LOADARR:
            # Load from Array
            regName = st.tuple[1]
            reg = self.registers.get(regName)
            indexRegName = st.tuple[2][1]
            indexReg = self.registers.get(indexRegName)
            arrayName = st.tuple[2][0]
            array = self.fetchValue(self.currentBlock,arrayName)
            if indexReg.t != LexName.INT:
                raise SemanticException("Array index must be INT")
            else:
                reg.value = array.value[indexReg.value].value
                reg.t = array.t

        elif st.operation == Tnames.PUSH:
            regName = st.tuple[1]
            reg = self.registers.get(regName)
            self.stack.append(reg.toTVariable())
        elif st.operation == Tnames.POP:
            regName = st.tuple[1]
            reg = self.registers.get(regName)
            val = self.stack.pop()
            reg.t = val.tp()
            reg.value = val.value

        elif st.operation == LexName.NOT:
            regName = st.tuple[1]
            reg = self.registers.get(regName)
            booleanValue = reg.booleanValue()
            if reg.t == LexName.BOOL:
                reg.value = not booleanValue
            else:
                raise SemanticException("Can't invert non-boolean value")
        elif st.operation in LexName.Operators:
            operation = st.operation
            op1 = st.tuple[1]
            op2 = st.tuple[2]
            src = self.registers.get(op2)
            dest = None
            if isinstance(op1,list):
            # TODO operation with arrays
                indexReg = self.registers.get(op1[1])
                if indexReg.t != LexName.INT:
                    raise SemanticException("Array index is not INT")
                arrayName = op1[0]
                array = self.fetchValue(self.currentBlock,arrayName).value
                dest = array[indexReg.value]
            else:
                name = op1
                if "_t" in name:
                    dest = self.registers.get(name)
                else:
                    dest = self.fetchValue(self.currentBlock, name)
            if not Operation.operationDefined(operation,dest.tp(),src.tp()):
                raise SemanticException(operation+" is not defined to "+dest.tp() + " "+src.tp())
            if operation == LexName.ASSIGN:
                if src.value is None:
                    dest.value = None
                elif src.t == LexName.INT and dest.t == LexName.FLOAT:
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
                    if src.t == LexName.INT and dest.t == LexName.FLOAT:
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
