from lexer import Token



class Interpreter(object):
    def __init__(self, text):
        # client string input, e.g. "3+5"
        self.text = text
        # self.pos is an index into self.text
        self.pos = 0
        # current token instance
        self.current_token = None


    def eat(self, token_type):
        # compare the current token type with the passed token
        # type and if they match then "eat" the current token
        # and assign the next token to the self.current_token,
        # otherwise raise an exception.
        # if self.current_token.type == token_type:
        #     self.current_token = self.get_next_token()
        # else:
        #     self.error()
        return None

    def expr(self):
        # set current token to the first token taken from the input
        # self.current_token = self.get_next_token()

        raise Exception("NOT YET")


def main():
    while True:
        try:
            text = input('calc> ')
        except EOFError:
            break
        if not text:
            continue
        interpreter = Interpreter(text)
        result = interpreter.expr()
        print(result)


if __name__ == '__main__':
    main()