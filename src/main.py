# from Interpreter import Interpreter
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
    print("Lexer start")
    param = Token.readLanguageDefinition("param/reserved.txt")
    print("Lexer initialization end")
    lexer = Lexer("file.txt")
    lexer.lexerize()
    print(lexer.tokenList)
    for token in lexer.tokenList:
        if token.type == LexName.LEXER_ERROR:
            raise Exception(token.__str__())
    parser = Parser(lexer.tokenList)
    beforeParsing = len(parser.tokenList)
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
    if beforeParsing != parser.tokenList.__len__():
        print("Mistakes were found at:")
        for token in parser.tokenList:
            if token.value is None:
                print(token)
        print("Before:" + str(beforeParsing) + " After: " + str(parser.tokenList.__len__()))
    # print(root.xml())
    w = open("AST.xml","w")
    w.write(root.xml())
    # print(Token.getSortedKeys(Token.other))
    print("END")
