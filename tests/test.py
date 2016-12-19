import inspect
import os

from src.Interpreter import Interpreter
from src.TAC import TACgen

root = Interpreter.simpleTest("t1")
# print(root.xml())
t = TACgen()
t.parseRoot(root)
print("\n\n")
for k in t.getStatementsAsString():
    print(k.__str__())
print("_________")
'''
for k in TACgen.getTabbedStatements(t.getOrderedListOfStatements(t.rootLabel)):
    print(k.__str__())
'''
for label in t.scopes.keyOrder:
    print(t.scopes.get(label).getBlockInfo())

i = Interpreter(t.scopes)
i.interpretBlock(t.rootLabel)
print("\n\n\n\n")
for s in i.scopes.returnItemsInOrder():
    print(s.getBlockInfo())