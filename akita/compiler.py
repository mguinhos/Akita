from os import path

from .tokenizer import Keyword, Literal, Comment, Name
from .tokenizer import tokenize, Token
from .parser import BinaryOperation, Call, Class, Def, Body, Import, Item, Attribute, Return, Set, List, AnyOperand
from .parser import If, Elif, Else, While, For
from .parser import parse

NEWLINE = '\n'
SOFTTAB= ' ' * 4

class Namespace:
    def __init__(self, variables: list[Name]=list(), functions: dict[tuple, Name]=dict()):
        self.variables = variables
        self.functions = functions
    
    def __repr__(self):
        return f'Namespace({self.variables})'

def compile_expression(namespace: Namespace, operand: AnyOperand):
    if type(operand) is Name:
        return operand.value
    elif type(operand) is Literal:
        if type(operand.value) is str:
            return '"%s"' % operand.value.replace('"', r'\"')

        return operand.value
    
    elif type(operand) is List:
        return f'{{{", ".join(compile_expression(namespace, item) for item in operand.items)}}}'
    
    elif type(operand) is Item:
        operand.head.hint = get_hint(namespace, operand.head)

        return f'{operand.head.value}[{compile_expression(namespace, operand.indice)}]'
    
    elif type(operand) is Attribute:
        if type(operand.name) is not Call:
            raise NotImplementedError
        
        if not operand.name.name.value.startswith(operand.head.value):
            operand.name.name = Name(operand.head.value + '__' + operand.name.name.value, operand.name.hint)

        return compile_call(namespace, operand.name)

    elif type(operand) is Call:
        return compile_call(namespace, operand)
    
    elif type(operand) is BinaryOperation and operand.hint == 'str':
        if operand.right.hint is None:
            operand.right.hint = get_hint(namespace, operand.right)
        
        if operand.left.hint is None:
            operand.left.hint = get_hint(namespace, operand.left)

        if operand.operator is Token.Equal:
            return f'strcmp({compile_expression(namespace, operand.left)}, {compile_expression(namespace, operand.right)}) == 0'
        elif operand.operator is Token.NotEqual:
            return f'strcmp({compile_expression(namespace, operand.left)}, {compile_expression(namespace, operand.right)}) != 0'
        
        return f'cat({compile_expression(namespace, operand.left)}, {compile_expression(namespace, operand.right)})'
        
        
    return f'{compile_expression(namespace, operand.left)} {operand.operator.value} {compile_expression(namespace, operand.right)}'

def get_hint(namespace: Namespace, operand: AnyOperand):
    if type(operand) is Name and operand in namespace.variables:
        return namespace.variables[namespace.variables.index(operand)].hint
    elif type(operand) is Call:
        if operand.name == 'str':
            return Name('str', Name('type'))

        return get_function(namespace, operand).rethint
    elif type(operand) is BinaryOperation:
        operand.hint = get_hint(namespace, operand.left)
    elif type(operand) is Item:
        hint = get_hint(namespace, operand.head)

        if hint.value == "str":
            return Name('char', Name('type'))
        elif hint.value == "list__str__":
            return Name('str', Name('type'))
        
        return hint
    
    elif type(operand) is Attribute:
        if type(operand.name) is not Call:
            raise NotImplementedError
    
        operand.name.name = Name(operand.head.value + '__' + operand.name.name.value)

        return get_hint(namespace, operand.name)
    
    elif type(operand) is List:
        operand.hint = get_hint(namespace, operand.items[0])
        return Name(f'list__{operand.hint.value}__', Name('type'))

    return operand.hint

def get_function(namespace: Namespace, call: Call):
    if (functions := namespace.functions.get(call.name)) is None:
        raise NameError(f'there is no function named `{call.name.value}`')
    
    call_signature = tuple(get_hint(namespace, arg) for arg in call.args)

    if call_signature not in functions:
        print(functions)
        raise Exception(f'function with signature `{call.name.value}({", ".join((sign.value if sign else "?") for sign in call_signature)})` does not exists')

    return functions[call_signature]

def compile_call(namespace: Namespace, call: Call):
    function = get_function(namespace, call)
    return f'{function.name.value.replace(".", "__")}({", ".join(str(compile_expression(namespace, arg)) for arg in call.args)})'

def compile_body(namespace: Namespace, body: Body, indent=0):
    INDENTTAB = SOFTTAB * indent
    NEWLINEINDENT = NEWLINE + INDENTTAB

    def compile(ast):
        if type(ast) is Comment:
            if ast.value.startswith('emit '):
                return ast.value.removeprefix('emit ')
            
            return f'// {ast.value}'
        elif type(ast) is Keyword:
            return f'{ast.value};'
        
        elif type(ast) is Attribute:
            if type(ast.name) is not Call:
                raise NotImplementedError
        
            ast.name.name = Name(ast.head.value + '__' + ast.name.name.value)

            return f'{compile_call(namespace, ast.name)};'

        if type(ast) is Return:
            return f'return {compile_expression(namespace, ast.operand)};'
        elif type(ast) is Call:
            return f'{compile_call(namespace, ast)};'
        elif type(ast) is Set:
            if ast.name.hint is None:
                ast.name.hint = get_hint(namespace, ast.name)
            
            if ast.name.hint is None:
                ast.name.hint = get_hint(namespace, ast.value)

            if ast.name in namespace.variables:
                if ast.name.hint != (name := namespace.variables[namespace.variables.index(ast.name)]).hint:
                    raise TypeError(f'variable `{name.value}` is of type `{name.hint.value}`, but a `{ast.name.hint.value}` was provided')
                
                if ast.name.hint.value == 'str' and ast.token is Token.PlusEqual:
                    return f'{ast.name.value} = cat({ast.name.value}, {compile_expression(namespace, ast.value)});'
                
                return f'{ast.name.value} {ast.token.value} {compile_expression(namespace, ast.value)};'
            
            namespace.variables.append(ast.name)

            if type(ast.value) is List:
                return f'{ast.name.hint.value} {ast.name.value}[] = {compile_expression(namespace, ast.value)};{NEWLINEINDENT}int len_{ast.name.value} = {len(ast.value.items)};'

            return f'{ast.name.hint.value} {ast.name.value} = {compile_expression(namespace, ast.value)};'
        
        elif type(ast) is If:
            return f'if ({compile_expression(namespace, ast.operand)}){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}'
        elif type(ast) is Elif:
            return f'else if ({compile_expression(namespace, ast.operand)}){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}'
        elif type(ast) is Else:
            return f'else{NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}'

        elif type(ast) is While:
            return f'while ({compile_expression(namespace, ast.operand)}){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}'
        elif type(ast) is For:
            if ast.operand.hint is None:
                ast.operand.hint = get_hint(namespace, ast.operand)
            
            if type(ast.operand.hint) is Item:
                ast.operand.hint = ast.operand.hint.hint
            
            if ast.operand.hint == "str_iterator_p":
                if ast.name not in namespace.variables:
                    ast.name.hint = Name('str', Name('type'))
                    namespace.variables.append(ast.name)
                
                return f'str_iterator_p {ast.name.value}_iterator = {compile_expression(namespace, ast.operand)};{NEWLINEINDENT}for (str {ast.name.value}=next({ast.name.value}_iterator); !{ast.name.value}_iterator->stopped; {ast.name.value} = next({ast.name.value}_iterator)){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}'
            elif ast.operand.hint == "str":
                if ast.name not in namespace.variables:
                    ast.name.hint = Name('char', Name('type'))
                    namespace.variables.append(ast.name)

                return f"str {ast.name.value}_iterator = {compile_expression(namespace, ast.operand)};{NEWLINEINDENT}for (char {ast.name.value}={ast.name.value}_iterator++[0]; {ast.name.value} != '\\0'; {ast.name.value} = {ast.name.value}_iterator++[0]){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}"
            
            elif ast.operand.hint == "list__str__":
                if ast.name not in namespace.variables:
                    ast.name.hint = Name('str', Name('type'))
                    namespace.variables.append(ast.name)
                
                if type(ast.operand) is List:
                    return f"list__str__ items[] = {compile_expression(namespace, ast.operand)};{NEWLINEINDENT}int len_items = {len(ast.operand.items)};{NEWLINEINDENT}int index_items = 0;{NEWLINEINDENT * 2}for (str {ast.name.value}=items[index_items]; index_items < len_items; {ast.name.value} = items[++index_items]){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}"

                return f"int index_{ast.operand.value} = 0;{NEWLINEINDENT * 2}for (str {ast.name.value}={ast.operand.value}[index_{ast.operand.value}]; index_{ast.operand.value} < len_{ast.operand.value}; {ast.name.value} = {ast.operand.value}[++index_{ast.operand.value}]){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}"

            if ast.name not in namespace.variables:
                ast.name.hint = Name('int', Name('type'))
                namespace.variables.append(ast.name)

            return f'for (int {ast.name.value}=0; {ast.name.value} < {compile_expression(namespace, ast.operand)}; {ast.name.value}++){NEWLINEINDENT}{{{compile_body(namespace, ast.body, indent +1)}{NEWLINEINDENT}}}'

        return ast

    return "".join(f'{NEWLINEINDENT}{compile(line)}' for line in body.lines)

def compile_type(namespace: Namespace, name: Name):
    if name is None:
        return Name('void')
    elif type(name) is Item:
        return Name(f'{name.head.value}__{name.indice.value}__')
    elif type(name) is Name:
        return name

    return name

def compile_def(namespace: Namespace, ast: Def, prefix: Name=None):
    if prefix:
        ast.name = Name(prefix.value + '.' + ast.name.value, ast.name or ast.rethint)

    local_namespace = Namespace(list(namespace.variables), namespace.functions)
    local_namespace.variables.extend(ast.args)

    if ast.name in namespace.functions:
        new_name = f'{ast.name.value.replace(".", "__")}_{"_".join(compile_type(namespace, arg.hint).value for arg in ast.args)}{"_" + ast.name.hint.value if ast.name.hint else ""}'
        
        namespace.functions[ast.name].update({tuple(compile_type(namespace, sign) for sign in ast.signature): Def(Name(new_name), ast.args, ast.body, ast.rethint)})

        return f'{compile_type(namespace, ast.rethint).value} {new_name}({", ".join(compile_type(namespace, arg.hint).value + " " + arg.value for arg in ast.args)}){NEWLINE}{{{compile_body(local_namespace, ast.body, indent=1)}{NEWLINE}}}'
    
    namespace.functions[ast.name] = {tuple(compile_type(namespace, sign) for sign in ast.signature): ast}

    return f'{ast.rethint.value if ast.rethint else "void"} {ast.name.value.replace(".", "__")}({", ".join(compile_type(namespace, arg.hint).value + " " + arg.value + ("[]" if compile_type(namespace, arg.hint).value.startswith("list") else "") for arg in ast.args)}){NEWLINE}{{{compile_body(local_namespace, ast.body, indent=1)}{NEWLINE}}}'

def compile_class(namespace: Namespace, ast: Class):
    return f'\n'.join(compile_def(namespace, function, prefix=ast.name) for function in ast.body.lines)


def compile(ast, namespace=Namespace(), path='.'):
    if type(ast) is Def:
        return compile_def(namespace, ast)
    
    elif type(ast) is Class:
        return compile_class(namespace, ast)
    
    elif type(ast) is Import:
        compile_filename(f'{path}/{ast.module.value}.py', namespace)
        return f'#include "{ast.module.value}.py.c"'

    elif type(ast) is Comment:
        if ast.value.startswith('emit '):
            return f'{ast.value.removeprefix("emit ")}'

        return f'// {ast.value}'

    return ast

def compile_filename(name: str, namespace=Namespace()):
    output = open(f'{name}.c', 'w')

    for ast in parse(tokenize(open(name))):
        output.write(compile(ast, namespace, path.dirname(name)))
        output.write('\n')
    
    return
