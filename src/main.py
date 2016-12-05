# from Interpreter import Interpreter
from src.ASTnodes import Root
from src.Interpreter import Interpreter
from src.LexNames import LexName
from src.lexer import Token, Lexer
from src.parser import Parser


def main():
    while True:
        try:
            text = input("feed me> ")
        except EOFError:
            break
        if not text:
            continue
        # it = Interpreter(text)
        # result = it.expr()
        # print(result)





if __name__ == '__main__':
    root = Interpreter.prepateAST("file.txt")
    w = open("AST.xml","w")
    w.write(root.xml())
    # print(Token.getSortedKeys(Token.other))
    print("END")
