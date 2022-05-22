from .tokenizer import Indent, TokenHook
from .tokenizer import Token, Keyword, Name, Literal, Comment

class Body:
    def __init__(self, lines: tuple["AnyAst"]):
        self.lines = lines
    
    def __repr__(self):
        return f'Body({self.lines})'

class Def:
    def __init__(self, name: Name, args: tuple[Name], body: Body, rethint: Name=None):
        self.name = name
        self.args = args
        self.body = body
        self.rethint = rethint
    
    def __repr__(self):
        return f'Def({self.name}, {self.args}, {self.body})'
    
    @property
    def signature(self):
        return tuple(arg.hint for arg in self.args)

class Class:
    def __init__(self, name: Name, body: Body):
        self.name = name
        self.body = body
    
    def __repr__(self):
        return f'Class({self.name}, {self.body})'

class Call:
    def __init__(self, head: "AnyOperand", args: tuple["AnyOperand"], hint=None):
        self.head = head
        self.args = args
        self.hint = hint
    
    def __repr__(self):
        return f'Call({self.name}, {self.args})'
    
    @property
    def name(self):
        if type(self.head) is Name:
            return self.head
        
        return self.head.name

class BinaryOperation:
    def __init__(self, operator: Token, left: "AnyOperand", right: "AnyOperand"):
        self.operator = operator
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f'BinaryOperation({self.operator}, {self.left}, {self.right})'

    @property
    def hint(self):
        if self.operator in (Token.EqualEqual, Token.NotEqual, Token.LessThan, Token.GreaterThan):
            return Name('bool', hint=Name('type'))

        if hint := self.left.hint:
            return hint
        
        return self.right.hint
    
    @hint.setter
    def hint(self, value: Name):
        if self.hint is None:
            self.left.hint = value
            self.right.hint = value
        
        return

AnyOperand = BinaryOperation | Name | Literal

class Import:
    def __init__(self, module: Name, names: tuple[Name]):
        self.module = module
        self.names = names
    
    def __repr__(self):
        return f'Import({self.module}, {self.names})'

class Return:
    def __init__(self, operand: AnyOperand):
        self.operand = operand
    
    def __repr__(self):
        return f'Return({self.operand})'

class If:
    def __init__(self, operand: AnyOperand, body: Body):
        self.operand = operand
        self.body = body
    
    def __repr__(self):
        return f'If({self.operand}, {self.body})'

class Elif(If):
    def __repr__(self):
        return f'Else({self.operand}, {self.body})'

class Else(If):
    def __init__(self, body: Body):
        self.body = body

    def __repr__(self):
        return f'Else({self.body})'

class While(If):
    def __repr__(self):
        return f'While({self.operand}, {self.body})'

class For(While):
    def __init__(self, name: Name, operand: AnyOperand, body: Body):
        self.name = name
        self.operand = operand
        self.body = body

    def __repr__(self):
        return f'For({self.name}, {self.operand}, {self.body})'

class Item:
    def __init__(self, head: AnyOperand, indice: AnyOperand):
        self.head = head
        self.indice = indice
    
    def __repr__(self):
        return f'Item({self.head}, {self.indice})'
    
    @property
    def hint(self):
        if self.head == 'list':
            return Name(f'{self.head.value}__{self.indice.value}__')

        return self.head.hint

class List:
    def __init__(self, items: list[AnyOperand], hint=None):
        self.items = items
        self.hint = hint
    
    def __repr__(self):
        return f'List({self.items})'
    
    @property
    def signature(self):
        return Name(f'list__{self.hint.value}__', self.hint)

class Attribute:
    def __init__(self, head: AnyOperand, body: list[AnyOperand]):
        self.head = head
        self.body = body
    
    def __repr__(self):
        return f'Attribute({self.head}, {self.body})'
    
    @property
    def hint(self):
        return self.body.hint
    
    @property
    def name(self) -> Name:
        return Name(f'{self.head.value}.{".".join(name.value for name in self.body)}')

class Set:
    def __init__(self, name: Name, token: Token, value: AnyOperand):
        self.name = name
        self.token = token
        self.value = value
    
    def __repr__(self):
        return f'Set({self.name}, {self.token}, {self.value})'

AnyAst = Body | Def

def parse_call(hook: TokenHook, name: Name):
    args = []

    for token in hook:
        if token is Token.RightParenthesis:
            break

        args.append(parse_expression(hook, token))

        token = hook.take()

        if token is Token.RightParenthesis:
            break
        elif token is not Token.Comma:
            raise SyntaxError(f'missing `,` at `{name.value}(...)`. found `{token}`')
        
    return Call(name, args)

def parse_item(hook: TokenHook, head: AnyOperand) -> Item:
    expression = parse_expression(hook, hook.take())
    token = hook.take()

    if token is not Token.RightBracket:
        raise SyntaxError(f'missing `]`at {head}')

    return Item(head, expression)

def parse_list(hook: TokenHook) -> List:
    items = []

    for token in hook:
        if token is Token.RightBracket:
            break
        elif token is Token.Comma:
            continue

        items.append(parse_expression(hook, token))

    return List(items)

def parse_attribute(hook: TokenHook, value: Name) -> AnyOperand:
    body = []

    for token in hook:
        body.append(parse_expression(hook, token, {Token.Dot}))
        token = hook.take()
        
        if token is not Token.Dot:
            hook.drop()
            break

    return Attribute(value, body)

def parse_expression(hook: TokenHook, value: AnyOperand, accept=set()) -> AnyOperand:

    if value is Token.LeftBracket:
        return parse_list(hook)

    if type(value) is Token or type(value) is Keyword:
        raise SyntaxError(f'expected expression, found `{value}`')
    
    token = hook.take()

    if accept and token not in accept:
        hook.drop()
        return value

    if token in (Token.Plus, Token.Minus, Token.Star, Token.Slash, Token.LessThan, Token.GreaterThan, Token.EqualEqual, Token.NotEqual):
        return BinaryOperation(token, value, parse_expression(hook, hook.take()))
    elif token is Token.Dot:
        return parse_expression(hook, parse_attribute(hook, value))
    elif token is Token.LeftParenthesis:
        return parse_expression(hook, parse_call(hook, value))
    elif token is Token.LeftBracket:
        return parse_expression(hook, parse_item(hook, value))
    else:
        hook.drop()
    
    return value

def parse_body(hook: TokenHook):
    token = hook.take()

    if token is not Token.Colon:
        raise SyntaxError(f'expecting `:`, found `{token}`')

    indent = hook.take()

    if type(indent) is not Indent:
        raise SyntaxError(f'expecting indent, found `{token}`')

    lines = []

    for token in hook:
        if token is Token.Eof:
            break
        elif token is Keyword.Pass:
            continue

        if type(token) is Indent:
            if token.value < indent.value:
                leave = True

                for token in hook:
                    if type(token) is not Indent:
                        hook.drop()
                        leave = True
                        break

                    if token.value >= indent.value:
                        hook.drop()
                        leave = False
                        break

                if leave:
                    break
        
        elif token is Token.Ellipsis:
            lines.append(token)
        elif token is Keyword.Return:
            lines.append(Return(parse_expression(hook, hook.take())))
        elif token in (Keyword.Break, Keyword.Continue):
            lines.append(token)
        elif token is Keyword.While:
            lines.append(While(parse_expression(hook, hook.take()), parse_body(hook)))
        elif token is Keyword.Def:
            lines.append(parse_def(hook))
        elif token is Keyword.Class:
            lines.append(parse_class(hook))
        elif token is Keyword.For:
            name = hook.take()

            if (token := hook.take()) is not Keyword.In:
                raise SyntaxError(f'expecting keyword `in` found `{token}`')

            lines.append(For(name, parse_expression(hook, hook.take()), parse_body(hook)))
        
        elif token is Keyword.If:
            lines.append(If(parse_expression(hook, hook.take()), parse_body(hook)))
        elif token is Keyword.Elif:
            lines.append(Elif(parse_expression(hook, hook.take()), parse_body(hook)))
        elif token is Keyword.Else:
            lines.append(Else(parse_body(hook)))
        
        elif type(token) is Name:
            name = token
            token = hook.take()

            if token is Token.Colon:
                name.hint = parse_expression(hook, hook.take())
                token = hook.take()

            if token in (Token.Equal, Token.PlusEqual, Token.MinusEqual, Token.StarEqual, Token.SlashEqual):
                expression = parse_expression(hook, hook.take())
                
                if name.hint is None:
                    name.hint = expression.hint
                
                lines.append(Set(name, token, expression))
            else:
                hook.drop()
                lines.append(parse_expression(hook, name))
        else:
            lines.append(parse_expression(hook, token))
    
    if token:
        hook.drop()

    return Body(lines)

def parse_def(hook: TokenHook):
    name = hook.take()

    if type(name) is not Name:
        raise TypeError(f'expected function name, found `{name}`')

    token = hook.take()

    if token is not Token.LeftParenthesis:
        raise SyntaxError(f'missing `(` at `def {name.value}(....)`')
    
    args = []

    for token in hook:
        if token is Token.RightParenthesis:
            break

        if type(token) is Name:
            args.append(token)
            token = hook.take()
            
            if token is Token.Colon:
                args[-1].hint = parse_expression(hook, hook.take())
                token = hook.take()
            
            if token is Token.RightParenthesis:
                break
            elif type(token) is Name:
                raise SyntaxError(f'missing comma for argument separator at `def {name.value}(...{token}...)`')
            elif token is not Token.Comma:
                raise SyntaxError(f'unexpected `{token}` at `def {name.value}({", ".join(arg.value for arg in args)}...)`')
        else:
            raise SyntaxError(f'unexpected `{token}` at `def {name.value}({", ".join(arg.value for arg in args)}...)`')
    
    token = hook.take()

    if token is not Token.Arrow:
        hook.drop()
        return Def(name, args, parse_body(hook))

    rethint = parse_expression(hook, hook.take())
    
    return Def(name, args, parse_body(hook), rethint)

def parse_class(hook: TokenHook) -> Class:
    return Class(hook.take(), parse_body(hook))
    
def parse(hook: TokenHook):
    for token in hook:
        if token is Token.Eof:
            break
        elif type(token) is Indent:
            continue

        if token is Keyword.Def:
            yield parse_def(hook)
        elif token is Keyword.Class:
            yield parse_class(hook)
        elif type(token) is Comment:
            yield token
        elif token is Keyword.Import:
            yield Import(hook.take())
        elif token is Keyword.From:
            name = hook.take()

            if type(name) is not Name:
                raise SyntaxError(f'expected name to import found `{name}`')
            
            if (keyword := hook.take()) is not Keyword.Import:
                raise SyntaxError(f'expected keyword `import` found `{keyword}`')

            yield Import(name, hook.take())
        else:
            raise SyntaxError(f'unexpected token `{token}`')
    
    return