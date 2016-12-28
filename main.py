import sys
from src.Interpreter import Interpreter






if __name__ == '__main__':
    try:
        debug = False
        if len(sys.argv)<2:
            print("Usage: file [debug] [optimize]")
            print("defaults: debug = False, optimize = True")
        else:
            if len(sys.argv)>2:
                debug = bool(sys.argv[2])
            time = Interpreter.simpleTest(sys.argv[1],debug)
            print("Succesfull execution")
            print(time[2])
    except Exception as e:
        print(e)

