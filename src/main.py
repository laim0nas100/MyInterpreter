# from Interpreter import Interpreter
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
    print("Lexer start")
    param = Token.readLanguageDefinition("param/reserved.txt")
    print("Lexer initialization end")
    lexer = Lexer("file.txt")
    lexer.lexerize()
    print(lexer.tokenList)
    parser = Parser(lexer.tokenList)

    print("Blocks left and right matching: "+str(parser.countBlocks()))
    root = parser.root()
    while parser.needReparse:
        print("Reparsing")
        parser.needReparse = False
        root = parser.root()
        print("Updated token list")
        print(parser.tokenList)
    print("Updated token list")
    print(parser.tokenList)
    # print(root.xml())
    w = open("AST.xml","w")
    w.write(root.xml())
    # print(Token.getSortedKeys(Token.other))
    print("END")
