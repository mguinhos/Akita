from sys import argv

from akita import tokenizer

fnames = argv[1:] if argv[1:] else ['examples/hello_world.py']

for fname in fnames:
    print('tokenizing', fname, '!')
    print()
    
    for token in tokenizer.tokenize(open(fname)):
        print(token)
    
    print()
    print('done tokenizing', fname, '!')