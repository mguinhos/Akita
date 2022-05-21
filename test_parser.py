from sys import argv

from akita import tokenizer
from akita import parser

fnames = argv[1:] if argv[1:] else ['examples/hello_world.py']

for fname in fnames:
    print('parsing', fname, '!')
    print()
    
    for ast in parser.parse(tokenizer.tokenize(open(fname))):
        print(ast)
    
    print()
    print('done parsing', fname, '!')