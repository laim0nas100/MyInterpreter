import definitions
from src.LexNames import LexName
from src.lexer import Token, Lexer
from src.parser import Parser


class Interpreter(object):
    @staticmethod
    def prepateAST(file):
        print("Lexer start")
        Token.readLanguageDefinition(definitions.ROOT_DIR+"/src/param/reserved.txt")
        print("Lexer initialization end")
        lexer = Lexer(file)
        lexer.lexerize()
        print(lexer.tokenList)
        for token in lexer.tokenList:
            if token.type == LexName.LEXER_ERROR:
                raise Exception(token.__str__())
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
