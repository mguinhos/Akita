from akita import tokenizer

for token in tokenizer.tokenize(open('examples/hello_world.py')):
    print(repr(token))