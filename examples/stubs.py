#emit #define _CRT_NONSTDC_NO_DEPRECATE
#emit #define _CRT_SECURE_NO_DEPRECATE
#emit #define _CRT_SECURE_NO_WARNINGS

#emit #include <stdbool.h>
#emit #include <string.h>

#emit #include <malloc.h>
#emit #include <memory.h>
#emit #include <stdlib.h>
#emit #include <stdio.h>

# this are stubs for python interoperability

#emit #define str char*
#emit #define list__str__ char*
#emit #define p_list__str__ char*
#emit #define str_iterator_p str_iterator*
#emit #define FILE_p FILE*


#emit typedef struct str_iterator {
#emit  bool stopped;
#emit  str string;
#emit  int position;
#emit  str (*__next__)(struct str_iterator*);
#emit }
#emit str_iterator;

#emit #define ASCII_DEFAULT "\033[0m"
#emit #define ASCII_RED "\033[31m"

def panic(name: str, message: str):
    #emit fprintf(stderr, ASCII_RED "%s: %s\n" ASCII_DEFAULT, name, message);
    #emit exit(-1);
    pass

def panic(message: str):
    panic("panic", message)

class char:
    def __str__(value: char) -> str:
        #emit char* buffer = malloc(2);
        #emit buffer[0] = value;
        #emit buffer[1] = '\0';
        #emit return buffer;
        pass

class int:
    def __str__(value: int) -> str:
        #emit char* buffer = malloc(32 +1);
        #emit itoa(value, buffer, 10);
        #emit return buffer;
        pass

class str_iterator:
    def __next__(self: str_iterator_p) -> str:
        #emit if (self->string[self->position] == '\0')
        #emit {
        #emit  self->stopped = true;
        #emit  return "x";
        #emit }
        #emit char* buffer = char____str__(self->string[self->position++]);
        #emit return buffer;
        pass

class str:
    def __iter__(self: str) -> str_iterator_p:
        #emit str_iterator_p iterator = malloc(sizeof(str_iterator));
        #emit *iterator = (str_iterator) { false, self, 0, str_iterator____next__ };
        #emit return iterator;
        pass

    def __int__(self: str) -> int:
        #emit return atoi(self);
        pass

    def __float__(self: str) -> float:
        #emit return atof(self);
        pass

def iter(iterable: str) -> str_iterator_p:
    return str.__iter__(iterable)

def next(iterator: str_iterator_p) -> str:
    return str_iterator.__next__(iterator)

def print(value: char):
    #emit putchar(value);
    #emit putchar('\n');
    pass

def print(value: str):
    #emit puts(value);
    pass

def print(value: int):
    #emit printf("%i\n", value);
    pass

def print(value: float):
    #emit printf("%f\n", value);
    pass

def print(value: bool):
    if value:
        #emit puts("True");
        pass
    else:
        #emit puts("False");
        pass

def input(prompt: str) -> str:
    #emit printf("%s", prompt);
    #emit char* buffer = malloc(4096);
    #emit fgets(buffer, 1024, stdin);
    #emit buffer = realloc(buffer, strlen(buffer));
    #emit return buffer;
    pass

def input(prompt: str) -> int:
    #emit printf("%s", prompt);
    #emit char* buffer = malloc(4096);
    #emit fgets(buffer, 1024, stdin);
    #emit buffer = realloc(buffer, strlen(buffer));
    #emit return atoi(buffer);
    pass


def cat(left: str, right: str) -> str:
    #emit size_t length = strlen(left) + strlen(right);
    #emit char* buffer = malloc(length +1);
    #emit strcpy(buffer, left);
    #emit strcat(buffer, right);
    #emit return buffer;
    pass

#emit inline
def range(value: int) -> int:
    return value

#emit #define range(x) x

def len(obj: str) -> int:
    length = 0
    for _ in iter(obj):
        length += 1
    
    return length

def len(obj: list[str]) -> int:
    length = 0
    for _ in obj:
        length += 1
    
    return length


def _open(path: str, mode: str) -> FILE_p:
    file: FILE_p = 0
    #emit file = fopen(path, mode);

    if file == 0:
        panic("failed to open file `" + path + "`")

    return file

def _open(path: str) -> FILE_p:
    return open(path, "r")


class FILE:
    def read(stream: FILE_p, count: int) -> str:
        #emit size_t buffer_len = count;
        #emit char* buffer = malloc(count +1);
        #emit fread(buffer, 1, count, stream);
        #emit buffer[buffer_len] = '\0';
        #emit return buffer;
        pass

    def read(stream: FILE_p) -> str:
        size = 0
        #emit fseek(stream, 0L, SEEK_SET);
        #emit fseek(stream, 0L, SEEK_END);
        #emit size = ftell(stream);
        #emit fseek(stream, 0L, SEEK_SET);
        return FILE.read(stream, size)

    def write(stream: FILE_p, text: str):
        length = len(text)
        count = 0
        #emit count = fwrite(text, 1, length, stream);
        if count < length:
            panic("failed to write to file")