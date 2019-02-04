import io
import sys
from base import LispError
from scanner import Scanner
from evaluator import eval_lexemes
from parser_ import Parser
from compiler import compile_
from machine import Machine

if __name__ == '__main__':
    machine = Machine()

    while True:
        print('>>>', end=' ', flush=True)
        scanner = Scanner()
        tokens = []
        parser = Parser()

        while True:
            f = io.StringIO(sys.stdin.readline())
            
            try:
                tokens.extend(eval_lexemes(scanner.scan('<stdin>', f)))
            except LispError as error:
                print(error.fullstr())
                break

            if scanner.state == scanner.scan_whitespace:
                try:
                    parser.parse(tokens)
                except LispError as error:
                    print(error.fullstr())
                    break

                if len(parser.expr_stack) == 1:
                    try:
                        print(machine.exec_(compile_(parser.end())))
                    except LispError as error:
                        print(error.fullstr())

                    break

            print('...', end=' ', flush=True)
            