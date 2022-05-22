from stubs import *

def main(argc: int, argv: list[str]) -> int:
    print(argc)

    len_argv = argc
    for arg in argv:
        print(arg)