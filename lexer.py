

import re


class LexerError(Exception):
    """Error lanzado cuando hay un símbolo que no se puede tokenizar."""
    pass


class Token:
    """Representa un token individual."""

    def __init__(self, tipo: str, valor: str):
        self.tipo = tipo    # "identifier", "número", "+", etc.
        self.valor = valor  # el valor original: "x", "5", "+"

    def __repr__(self):
        return f"Token({self.tipo!r}, {self.valor!r})"


class Lexer:
   
    # Patrones en orden de prioridad
    TOKEN_PATTERNS = [
        ("número",     r'\d+(\.\d+)?'),       # 5, 3.14, 100
        ("identifier", r'[a-zA-Z_]\w*'),       # x, nombre, var_1
        ("op",         r'[+\-*/]'),            # operadores
        ("paren",      r'[()]'),               # paréntesis
        ("skip",       r'\s+'),                # espacios (ignorar)
    ]

    def __init__(self):
        # Compilar todos los patrones en uno solo (más eficiente)
        parts = [f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_PATTERNS]
        self._regex = re.compile('|'.join(parts))

    def tokenize(self, expression: str) -> tuple[list[str], list[str]]:
      
        if not expression.strip():
            raise LexerError("La expresión está vacía.")

        tokens = []
        descripciones = []
        pos = 0

        for match in self._regex.finditer(expression):
            # Detectar caracteres no reconocidos entre matches
            if match.start() != pos:
                bad = expression[pos:match.start()]
                raise LexerError(
                    f"Símbolo no reconocido: '{bad}'\n"
                    f"Solo se permiten: números, letras, +, -, *, /, (, )"
                )

            kind = match.lastgroup
            value = match.group()
            pos = match.end()

            if kind == "skip":
                continue  # ignorar espacios

            if kind == "número":
                tokens.append("número")
                descripciones.append(f"{value}→número")

            elif kind == "identifier":
                tokens.append("identifier")
                descripciones.append(f"{value}→identifier")

            elif kind in ("op", "paren"):
                tokens.append(value)
                descripciones.append(value)

        # Verificar que no haya caracteres al final sin procesar
        if pos != len(expression):
            bad = expression[pos:]
            raise LexerError(
                f"Símbolo no reconocido al final: '{bad}'\n"
                f"Solo se permiten: números, letras, +, -, *, /, (, )"
            )

        if not tokens:
            raise LexerError("No se encontraron tokens válidos en la expresión.")

        return tokens, descripciones

    def tokens_to_string(self, tokens: list[str]) -> str:
        """Convierte la lista de tokens a string separado por espacios."""
        return " ".join(tokens)


if __name__ == "__main__":
    lexer = Lexer()

    expresiones = [
        "5 + 2 * x",
        "a + b",
        "(a - b) * c",
        "x * 3.14 + y",
        "nombre + valor * resultado",
    ]

    for expr in expresiones:
        print(f"\nExpresión : {expr}")
        try:
            tokens, descrips = lexer.tokenize(expr)
            print(f"Tokens    : {tokens}")
            print(f"Conversión: {' | '.join(descrips)}")
        except LexerError as e:
            print(f"Error: {e}")
