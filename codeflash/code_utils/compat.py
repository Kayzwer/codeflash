import os

# os-independent newline
# make sure to use this in f-strings e.g. f"some string{LF}"
# you can use "[^f]\".+\{LF\}\" to find any lines in your code that use this without the f-string
LF: str = os.linesep
