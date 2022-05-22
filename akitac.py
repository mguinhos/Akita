#!/usr/bin/python3

from argparse import ArgumentParser
import os

from akita import compiler

# os specific stuff
if os.name == 'posix':
    EXECUTABLE_SUFIX= 'elf'
else:
    EXECUTABLE_SUFIX= 'exe'

argparser = ArgumentParser()
argparser.add_argument('file')

def main():
    args = argparser.parse_args()

    if filename := args.file:
        print(f'compiling `{filename}`')
        compiler.compile_filename(filename)
        os.system(f'clang {filename}.c -o {filename}.{EXECUTABLE_SUFIX}')
        print('done!')
        print(f'run with ./{filename}.{EXECUTABLE_SUFIX}')
        return

    return args.print_help()


if __name__ == '__main__':
    main()
