import sys
from src.Interpreter import Interpreter






if __name__ == '__main__':
    try:
        debug = False
        if len(sys.argv)>2:
            debug = bool(sys.argv[2])
        Interpreter.simpleTest(sys.argv[1],debug)
        print("Succesfull execution")
    except IndexError as e:
        print("Usage: file [debug]")
    except Exception as e:
        print(e)

