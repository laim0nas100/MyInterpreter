from src.Interpreter import Interpreter
from src.TAC import TAC, LexName, Tnames

i = Interpreter(None)
i.evaluate(TAC(Tnames.LOAD,"_t0",[LexName.TRUE,None]))
i.evaluate(TAC(Tnames.LOAD,"_t1",[LexName.INTEGER_CONST,2]))
print(i.stringRegisters())

print(DefinedOperation.operationDefined(LexName.PLUS,i.registers.get("_t0").t,i.registers.get("_t1").t))
