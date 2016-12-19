import os
class CustomException(Exception):
    pass
class LexerException(CustomException):
    pass
class ParserException(CustomException):
    pass
class SemanticException(CustomException):
    pass


HOME_DIR = os.path.dirname(os.path.abspath(__file__))
print(HOME_DIR)

