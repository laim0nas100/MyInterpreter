from Interpreter import Interpreter
from lexer import Token, Lexer


def main():
    while True:
        try:
            text = input("feed me> ")
        except EOFError:
            break
        if not text:
            continue
        it = Interpreter(text)
        result = it.expr()
        print(result)

if __name__ == '__main__':
    print("Lexer start")
    param = Token.readLanguageDefinition("reserved.txt")
    print("Lexer initialization end")
    lexer = Lexer("file.txt")
    print()
    print(Token.keywords)
    print(Token.other)
    lexer.lexerize()
    # print(lexer.tokenList)
    for token in lexer.tokenList:
        print(token)
    print("END")