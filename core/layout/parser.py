# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import List, Dict, Any, Optional, Tuple
import re
import numpy as np


class LayoutToken:
    IDENT = "IDENT"
    STRING = "STRING"
    NUMBER = "NUMBER"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    COLON = "COLON"
    COMMA = "COMMA"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


class Token:
    def __init__(self, type: str, value: Any, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.line}:{self.column})"


class LayoutLexer:
    """Optimized lexer using regex-based block processing for faster parsing."""
    
    TOKEN_PATTERNS = [
        (r'#[^\n]*', lambda m: ('COMMENT', m.group(0)[1:])),  # Comments
        (r'"[^"]*"', lambda m: ('STRING', m.group(0)[1:-1])),  # Double-quoted strings
        (r"'[^']*'", lambda m: ('STRING', m.group(0)[1:-1])),  # Single-quoted strings
        (r'[0-9]+(?:\.[0-9]+)?', lambda m: ('NUMBER', float(m.group(0)))),  # Numbers
        (r'[a-zA-Z_][a-zA-Z0-9_-]*', lambda m: ('IDENT', m.group(0))),  # Identifiers
        (r'\{', lambda m: ('LBRACE', '{')),
        (r'\}', lambda m: ('RBRACE', '}')),
        (r':', lambda m: ('COLON', ':')),
        (r',', lambda m: ('COMMA', ',')),
        (r'\n', lambda m: ('NEWLINE', '\n')),
        (r'[ \t]+', lambda m: None),  # Skip whitespace
    ]
    
    def __init__(self, text: str):
        self.text = text
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self._compiled_pattern = None

    def _build_pattern(self):
        """Build combined regex pattern for efficient matching."""
        pattern_parts = []
        for pattern, _ in self.TOKEN_PATTERNS:
            pattern_parts.append(f'({pattern})')
        self._compiled_pattern = re.compile('|'.join(pattern_parts))

    def _get_line_col(self, pos: int) -> Tuple[int, int]:
        """Calculate line and column from position."""
        line = self.text[:pos].count('\n') + 1
        last_newline = self.text.rfind('\n', 0, pos)
        col = pos - last_newline if last_newline >= 0 else pos + 1
        return line, col

    def tokenize(self) -> List[Token]:
        """Tokenize using regex for O(n) performance instead of character-by-character O(n²)."""
        if not self.text:
            self.tokens.append(Token(LayoutToken.EOF, None, 1, 1))
            return self.tokens
            
        self._build_pattern()
        
        matches = list(self._compiled_pattern.finditer(self.text))
        
        for match in matches:
            token_type, token_value = None, None
            
            for i, (_, handler) in enumerate(self.TOKEN_PATTERNS):
                if match.group(i + 1):
                    result = handler(match)
                    if result:
                        token_type, token_value = result
                    break
            
            if token_type is None:
                continue
                
            line, col = self._get_line_col(match.start())
            
            if token_type == 'COMMENT':
                continue
            elif token_type == 'NEWLINE':
                self.tokens.append(Token(LayoutToken.NEWLINE, '\n', line, col))
            elif token_type == 'LBRACE':
                self.tokens.append(Token(LayoutToken.LBRACE, '{', line, col))
            elif token_type == 'RBRACE':
                self.tokens.append(Token(LayoutToken.RBRACE, '}', line, col))
            elif token_type == 'COLON':
                self.tokens.append(Token(LayoutToken.COLON, ':', line, col))
            elif token_type == 'COMMA':
                self.tokens.append(Token(LayoutToken.COMMA, ',', line, col))
            elif token_type == 'STRING':
                self.tokens.append(Token(LayoutToken.STRING, token_value, line, col))
            elif token_type == 'NUMBER':
                self.tokens.append(Token(LayoutToken.NUMBER, token_value, line, col))
            elif token_type == 'IDENT':
                self.tokens.append(Token(LayoutToken.IDENT, token_value, line, col))
        
        # Calculate final position
        if matches:
            last_match = matches[-1]
            last_line, last_col = self._get_line_col(last_match.end())
            self.tokens.append(Token(LayoutToken.EOF, None, last_line, last_col))
        else:
            self.tokens.append(Token(LayoutToken.EOF, None, 1, 1))
        
        return self.tokens


class ASTNode:
    pass


class ElementNode(ASTNode):
    def __init__(self, type: str, id: Optional[str] = None):
        self.type = type
        self.id = id
        self.properties: Dict[str, Any] = {}
        self.children: List[ElementNode] = []

    def __repr__(self):
        return f"ElementNode({self.type}, id={self.id}, props={self.properties}, children={len(self.children)})"


class PropertyNode(ASTNode):
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value


class LayoutParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _advance(self) -> Token:
        token = self._current()
        self.pos += 1
        return token

    def _expect(self, token_type: str) -> Token:
        token = self._current()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type} at {token.line}:{token.column}, got {token.type}")
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._current().type == LayoutToken.NEWLINE:
            self._advance()

    def _parse_value(self) -> Any:
        token = self._current()
        if token.type == LayoutToken.NUMBER:
            self._advance()
            return token.value
        if token.type == LayoutToken.STRING:
            self._advance()
            return token.value
        if token.type == LayoutToken.IDENT:
            self._advance()
            return token.value
        if token.type == LayoutToken.LBRACE:
            return self._parse_object()
        return None

    def _parse_object(self) -> Dict[str, Any]:
        self._expect(LayoutToken.LBRACE)
        self._skip_newlines()
        obj = {}
        while self._current().type != LayoutToken.RBRACE:
            key_token = self._expect(LayoutToken.IDENT)
            self._expect(LayoutToken.COLON)
            self._skip_newlines()
            value = self._parse_value()
            obj[key_token.value] = value
            self._skip_newlines()
            if self._current().type == LayoutToken.COMMA:
                self._advance()
                self._skip_newlines()
        self._expect(LayoutToken.RBRACE)
        return obj

    def _parse_element(self) -> ElementNode:
        type_token = self._expect(LayoutToken.IDENT)
        element_type = type_token.value
        element_id = None

        if self._current().type == LayoutToken.STRING:
            id_token = self._advance()
            element_id = id_token.value
        elif self._current().type == LayoutToken.IDENT and self._current().value.startswith("#"):
            id_token = self._advance()
            element_id = id_token.value[1:]

        element = ElementNode(element_type, element_id)

        if self._current().type == LayoutToken.LBRACE:
            self._advance()
            self._skip_newlines()
            while self._current().type != LayoutToken.RBRACE:
                if self._current().type == LayoutToken.IDENT:
                    key_token = self._expect(LayoutToken.IDENT)
                    key = key_token.value
                    if self._current().type == LayoutToken.COLON:
                        self._expect(LayoutToken.COLON)
                        self._skip_newlines()
                        if self._current().type == LayoutToken.LBRACE:
                            element.properties[key] = self._parse_object()
                        elif self._current().type == LayoutToken.IDENT and self._current().value in ("row", "column", "grid"):
                            inline_type = self._advance()
                            element.properties[key] = {"type": inline_type.value}
                            if self._current().type == LayoutToken.STRING:
                                element.properties[key]["value"] = self._advance().value
                        else:
                            element.properties[key] = self._parse_value()
                        self._skip_newlines()
                        if self._current().type == LayoutToken.COMMA:
                            self._advance()
                            self._skip_newlines()
                    elif self._current().type == LayoutToken.NEWLINE:
                        self._skip_newlines()
                        if self._current().type == LayoutToken.IDENT:
                            child = self._parse_element()
                            element.children.append(child)
                        continue
                elif self._current().type == LayoutToken.IDENT:
                    child = self._parse_element()
                    element.children.append(child)
                else:
                    self._advance()
            self._expect(LayoutToken.RBRACE)
        return element

    def parse(self) -> List[ElementNode]:
        elements = []
        self._skip_newlines()
        while self._current().type != LayoutToken.EOF:
            if self._current().type == LayoutToken.IDENT:
                elements.append(self._parse_element())
            self._skip_newlines()
        return elements


def parse_layout_dsl(dsl_text: str) -> List[ElementNode]:
    lexer = LayoutLexer(dsl_text)
    tokens = lexer.tokenize()
    parser = LayoutParser(tokens)
    return parser.parse()