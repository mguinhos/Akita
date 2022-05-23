from stubs import *
from libc import *

def show(string: pointer[str]):
    puts(string)

def main() -> int:
    string: pointer[str] = "hello!"
    show(string)