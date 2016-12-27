import inspect
import os

from definitions import CustomException
from src.ASTnodes import FnParameter
from src.Interpreter import Interpreter
from src.LexNames import LexName
from src.SpecificTypes import TFunction
from src.TAC import TACgen
from src.lexer import Token
from src.lib import eprint

root = Interpreter.simpleTest("t1")
# print(root.xml())
t = TACgen()


def f1(ob: list):
    eprint(ob[0])
    return [LexName.NULL, ""]

def f2(ob :list):
    string = input()
    return [LexName.STRING,string]

def f3(ob:list):
    return [LexName.STRING,str(ob[0])]

def f4(ob:list):
    string = ob[0]
    try:
        i = int(string)
    except ValueError:
        i = 0
    return [LexName.INT,i]

def f5(ob:list):
    string = ob[0]
    index = ob[1]
    try:
        char = string[index]
    except Exception:
        char = None
    return [LexName.STRING,char]

t.addGlobalFunction(TFunction([LexName.NULL, False],Token.get(LexName.PRINT),"Global", [FnParameter(LexName.STRING, "ob")],f1))
t.addGlobalFunction(TFunction([LexName.STRING, False],Token.get(LexName.INPUT),"Global", [],f2))
t.addGlobalFunction(TFunction([LexName.STRING, False],"toStr","Global", [FnParameter(LexName.STRING, "ob")],f3))
t.addGlobalFunction(TFunction([LexName.INT, False],"toInt","Global", [FnParameter(LexName.STRING, "ob")],f4))
t.addGlobalFunction(TFunction([LexName.STRING, False],"charAt","Global",
                              [FnParameter(LexName.STRING, "ob"),FnParameter(LexName.INT, "i")],f5))
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
i.debug = True
i.globalFunctions = t.globalFunctions
i.interpretBlock(t.rootLabel)

print("\n\n\n\n")
for s in i.callStack:
    pass
    print(s.getBlockInfo())

print("End.")
