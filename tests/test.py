import inspect
import os

from src.Interpreter import Interpreter
from src.TAC import TACgen

root = Interpreter.simpleTest("t1")
print(root.xml())
t = TACgen()
l = t.parseBlock(root)
print("\n\n")
for k in l:
    print(k.__str__())
