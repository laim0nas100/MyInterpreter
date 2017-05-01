#import definitions
# Interpreter.optimizeTest("t1",True)
# Interpreter.simpleTest("t2",False)
from src.Interpreter import Interpreter


Interpreter.optimizeTest("script",True)
# rez1 = Interpreter.simpleTest("script",optimize=False)
# # rez2 = Interpreter.simpleTest("t1")
#
# print(rez1[2])
# inputBuffer = rez1[3]
# rez2 = Interpreter.simpleTest("script",optimize=True,inputBuffer=inputBuffer)
# print(rez2[2])

# Interpreter.simpleTest(definitions.HOME_DIR+"/script",True)
#