###############################################################################
#                                                                             #
#  LEXER                                                                      #
#                                                                             #
###############################################################################

# Token types
#
# EOF (end-of-file) token is used to indicate that
# there is no more input left for lexical analysis
import re
from lib import ArrayList, stringReplace

class Token(object):
    tokens = dict()
    keys = list()
    keywords = dict()
    other = dict()
    @staticmethod
    def getSortedKeys(diction:dict):
        valueArray = list()
        keyArray = list()
        result = list()
        for info in diction.items():
            keyArray.append([info[0],info[1]])

        keyArray.sort(key=lambda x: len(x[1]), reverse=True)
        for key in keyArray:
            result.append(key[0])
        return result
    @staticmethod
    def get(key):
        return Token.tokens.get(key)

    @staticmethod
    def setKeyword(key):
        Token.keywords.setdefault(key,Token.get(key))

    @staticmethod
    def readLanguageDefinition(file):

        file = open(file, 'r')
        array = ArrayList()

        for line in file.readlines():
            if line.__len__() > 1:
                array.append(stringReplace(line, '\n'))
        for line in array:
            arr = line.split(" ")
            Token.keys.append(arr[0])
            Token.tokens.setdefault(arr[0], arr[1])
        for key in Token.keys:
            value = Token.get(key)
            if value[0].isalpha():
                Token.setKeyword(key)

        for tokenKey in Token.keys:
            if not Token.keywords.__contains__(tokenKey):
                Token.other.setdefault(tokenKey,Token.get(tokenKey))



    def __init__(self, type, value):
        self.type = type
        self.value = value


    def __str__(self):
        """String representation of the class instance.
        Examples:
            Token(INTEGER, 3)
            Token(PLUS, '+')
            Token(MUL, '*')
        """
        return 'Token({type}, {value})'.format(
            type=self.type,
            value=repr(self.value)
        )

    def __repr__(self):
        return self.__str__()


class Pos:
    def __init__(self,line,index):
        self.linePos = line
        self.indexPos = index

    def __str__(self):
        return str(self.linePos)+":"+str(self.indexPos)


class Lexer(object):
    def __init__(self, text):
        file = open(text,"r")
        self.lines = file.readlines()
        self.text = self.lines[0]
        self.pos = Pos(0,0)
        self.tokenList = list()

    def error(self):
        raise Exception('Invalid character'+self.currentChar())

    def currentChar(self):
        try:
            return self.lines[self.pos.linePos][self.pos.indexPos]
        except Exception:
            return None

    def currentLineLen(self):
        return len(self.lines[self.pos.linePos])

    def getByPos(self,pos:Pos):
        try:
            return self.lines[pos.linePos][pos.indexPos]
        except Exception:
            return None

    def advance(self,amount=1):
        """Advance the `pos` pointer and set the `currentChar()` variable."""
        self.pos = self.rangeCheck(amount)


    def rangeCheck(self,shift:int)->Pos:
        try:
            pos = Pos(self.pos.linePos,self.pos.indexPos+shift)
            while pos.indexPos >= self.currentLineLen():
                pos.indexPos -= self.currentLineLen()
                pos.linePos += 1
                if pos.linePos>=self.lines.__len__():
                    pos.linePos = None
                    break
        except Exception:
            return Pos(None,None)
        return pos

    def peek(self, amount=1):
        pos = self.rangeCheck(amount)
        if pos.linePos is not None:
            return self.getByPos(pos)
        else:
            return None

    def skip_whitespace(self):
        while self.currentChar() is not None and self.currentChar().isspace():
            self.advance()

    def skip_comment(self):
        tk = Token.get("COMMENTEND")
        while not self.tryToMatch(tk):
            self.advance()
        self.advance(len(tk))

    def skipLine(self):
        self.pos.indexPos = 0
        self.pos.linePos +=1

    def number(self):
        """Return a (multidigit) integer or float consumed from the input."""
        result = ""
        while self.currentChar() is not None and self.currentChar().isdigit():
            result += self.currentChar()
            self.advance()

        if self.tryToMatch(Token.get("FLOATSIGN")):
            result += "."
            self.advance()

            while (
                self.currentChar() is not None and
                self.currentChar().isdigit()
            ):
                result += self.currentChar()
                self.advance()

            token = Token("FLOAT_CONST", float(result))
        else:
            token = Token("INTEGER_CONST", int(result))

        return token

    def string(self):
        result = ""
        self.advance()
        while self.currentChar() is not None and not self.tryToMatch(Token.get("STRINGR")):
            result += self.currentChar()
            self.advance()
        self.advance()
        return Token("STRING_CONST", str(result))

    def id(self):
        """Handle identifiers and reserved keywords"""
        result = ''
        while self.currentChar() is not None and self.currentChar().isalnum():
            result += self.currentChar()
            self.advance()
        # no longer read
        for key in Token.getSortedKeys(Token.keywords):
            tokenValue = Token.get(key)
            if result == tokenValue:
                token = Token(key,tokenValue)
                print(token)
                return token

        return Token("VARIABLE",result)

    def getNextToken(self):
        """Lexical analyzer (also known as scanner or tokenizer)
        This method is responsible for breaking a sentence
        apart into tokens. One token at a time.
        """
        while self.currentChar() is not None:
            print("Current:"+self.currentChar())

            if self.currentChar().isspace():
                self.skip_whitespace()
                continue

            if self.currentChar().isalpha():
                return self.id()

            if self.currentChar().isdigit():
                return self.number()

            if self.tryToMatch(Token.get("LINECOMMENT")):
                self.skipLine()
                continue
            if self.tryToMatch(Token.get("COMMENTSTART")):
                self.advance(len(Token.get("COMMENTSTART")))
                self.skip_comment()
                continue
            if self.tryToMatch(Token.get("STRINGL")):
                return self.string()
            for key in Token.getSortedKeys(Token.other):
                tokenValue = Token.get(key)
                if self.tryToMatch(tokenValue):
                    self.advance(len(tokenValue))
                    return Token(key,tokenValue)

            self.error()

        return Token("EOF", None)

    def variable(self):
        pass

    def tryToMatch(self, explicit:str):
        lengthToPeek = len(explicit)
        readSymbols = ""
        for i in range(0,lengthToPeek):

            ch = self.peek(i)
            if ch is not None:
                readSymbols+=ch

        # print(readSymbols)
        return readSymbols == explicit

    def lexerize(self,output=None):

        token = token = self.getNextToken()
        while token.type != "EOF":
            self.tokenList.append(token)
            token = self.getNextToken()
        if output is not None:
            file = open(output,"w")
            for token in self.tokenList:
                file.write(str(token)+"\n")

