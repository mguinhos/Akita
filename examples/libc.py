def malloc(size: int) -> int:
    ...

def free(address: int):
    ...

def puts(string: str):
    ...

def exit(status: int):
    ...

class pointer(Generic[T]):
    ...