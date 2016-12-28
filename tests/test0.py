import definitions
from src.Interpreter import Interpreter
# Interpreter.optimizeTest("t1",True)
# Interpreter.simpleTest("t2",False)


rez1 = Interpreter.simpleTest("t1",optimize=False)
rez2 = Interpreter.simpleTest("t1")
print(rez1[2])
print(rez2[2])

# Interpreter.simpleTest(definitions.HOME_DIR+"/script",True)
#