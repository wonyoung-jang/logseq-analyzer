"""
Parse EDN (Extensible Data Notation) data from Logseq configuration files.
"""

from typing import Any, Generator
import re
import ast

# Simple EDN tokenizer and parser to convert EDN data into Python types.
TOKEN_REGEX = re.compile(
    r"""
    "(?:\\.|[^"\\])*"         | # strings
    \#\{                      | # set literal
    \{|\}|\[|\]|\(|\)         | # delimiters
    [^"\s\{\}\[\]\(\),]+        # atoms (numbers, symbols, keywords, etc.)
    """,
    re.VERBOSE,
)


class LogseqConfigEDN:
    """
    A simple EDN parser that converts EDN data into Python data structures.
    """

    def __init__(self, tokens) -> None:
        """
        Initialize the parser with a list of tokens.
        """
        self.tokens = list(tokens)
        self.pos = 0

    def peek(self) -> Any | None:
        """
        Return the next token without advancing the position.
        """
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> Any | None:
        """
        Return the next token and advance the position.
        """
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> dict | list | set | Any | None | bool | float | int:
        """
        Parse the entire EDN input and return the resulting Python object.
        """
        value = self.parse_value()
        if self.peek() is not None:
            raise ValueError(f"Unexpected extra EDN data: {self.peek()}")
        return value

    def parse_value(self) -> dict | list | set | Any | None | bool | float | int:
        """
        Parse a single EDN value.
        """
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of EDN input")
        # Dispatch by token
        if tok == "{":
            return self.parse_map()
        if tok == "[":
            return self.parse_vector()
        if tok == "(":
            return self.parse_list()
        if tok == "#{":
            return self.parse_set()
        if tok.startswith('"'):
            return self.parse_string()
        if tok in ("true", "false", "nil"):
            return self.parse_literal()
        # Number, keyword, or symbol
        if self.is_number(tok):
            return self.parse_number()
        if tok.startswith(":"):
            return self.parse_keyword()
        return self.parse_symbol()

    def parse_map(self) -> dict:
        """
        Parse a map (dictionary) from EDN.
        """
        self.next()  # Consume '{'
        result = {}
        while True:
            tok = self.peek()
            if tok == "}":
                self.next()
                break
            # Parse key and value
            key = self.parse_value()
            val = self.parse_value()
            # Convert unhashable keys to hashable types
            if isinstance(key, dict):
                key = frozenset(key.items())
            elif isinstance(key, list):
                key = tuple(key)
            elif isinstance(key, set):
                key = frozenset(key)
            result[key] = val
        return result

    def parse_vector(self) -> list:
        """
        Parse a vector (list) from EDN.
        """
        self.next()
        result = []
        while True:
            tok = self.peek()
            if tok == "]":
                self.next()
                break
            result.append(self.parse_value())
        return result

    def parse_list(self) -> list:
        """
        Parse a list from EDN.
        """
        self.next()
        result = []
        while True:
            tok = self.peek()
            if tok == ")":
                self.next()
                break
            result.append(self.parse_value())
        return result

    def parse_set(self) -> set:
        """
        Parse a set from EDN.
        """
        self.next()  # Consume '#{'
        result = set()
        while True:
            tok = self.peek()
            if tok == "}":
                self.next()
                break
            result.add(self.parse_value())
        return result

    def parse_string(self) -> Any:
        """
        Parse a string from EDN.
        """
        tok = self.next()
        # Use ast.literal_eval for escape handling
        return ast.literal_eval(tok)

    def parse_literal(self) -> None | bool:
        """
        Parse a literal value from EDN.
        """
        tok = self.next()
        if tok == "true":
            return True
        if tok == "false":
            return False
        if tok == "nil":
            return None

    def is_number(self, tok) -> bool:
        """
        Check if the token is a valid number (integer or float).
        """
        return re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", tok) is not None

    def parse_number(self) -> float | int:
        """
        Parse a number (integer or float) from EDN.
        """
        tok = self.next()
        if "." in tok or "e" in tok or "E" in tok:
            return float(tok)
        return int(tok)

    def parse_keyword(self) -> Any | None:
        """
        Parse a keyword from EDN.
        """
        tok = self.next()
        return tok

    def parse_symbol(self) -> Any | None:
        """
        Parse a symbol from EDN.
        """
        tok = self.next()
        return tok


def loads(edn_str) -> dict | list | set | Any | None | bool | float | int:
    """
    Parse an EDN-formatted string and return the corresponding Python data structure.
    """
    tokens = tokenize(edn_str)
    parser = LogseqConfigEDN(tokens)
    return parser.parse()


def tokenize(edn_str) -> Generator[str, Any, None]:
    """
    Yield EDN tokens, skipping comments, whitespace, and commas.
    Comments start with ';' and run to end-of-line.
    Commas are treated as whitespace per EDN spec.
    """
    edn_str = re.sub(r";.*", "", edn_str)
    for match in TOKEN_REGEX.finditer(edn_str):
        tok = match.group().strip()
        yield tok
