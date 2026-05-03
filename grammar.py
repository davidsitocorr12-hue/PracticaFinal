

class Production:
   

    def __init__(self, head: str, bodies: list[list[str]]):
        self.head = head          # Símbolo del lado izquierdo, ej: "E"
        self.bodies = bodies      # Lista de alternativas, ej: [["E","+","T"], ["T"]]

    def __repr__(self):
        bodies_str = " | ".join(" ".join(b) for b in self.bodies)
        return f"{self.head} -> {bodies_str}"


class Grammar:
   

    def __init__(self):
        self.start_symbol: str = ""
        self.productions: dict[str, list[list[str]]] = {}
        self.terminals: set[str] = set()
        self.non_terminals: set[str] = set()

   
    def parse_from_string(self, text: str) -> None:
       
        self.productions.clear()
        self.terminals.clear()
        self.non_terminals.clear()
        self.start_symbol = ""

        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

        for i, line in enumerate(lines):
            if "->" not in line:
                raise ValueError(
                    f"Línea {i+1} inválida: '{line}'. "
                    f"Formato esperado: 'NoTerminal -> cuerpo1 | cuerpo2'"
                )

            head, _, body_str = line.partition("->")
            head = head.strip()

            if not head:
                raise ValueError(f"Línea {i+1}: el lado izquierdo está vacío.")

            # El primer no-terminal encontrado es el símbolo inicial
            if not self.start_symbol:
                self.start_symbol = head

            self.non_terminals.add(head)

            # Cada alternativa separada por "|"
            alternatives = body_str.split("|")
            bodies: list[list[str]] = []

            for alt in alternatives:
                symbols = alt.strip().split()
                if not symbols:
                    raise ValueError(
                        f"Línea {i+1}: alternativa vacía en producción de '{head}'."
                    )
                bodies.append(symbols)

            # Acumula si ya existía una producción para este no-terminal
            if head in self.productions:
                self.productions[head].extend(bodies)
            else:
                self.productions[head] = bodies

        self._infer_terminals()

    def _infer_terminals(self) -> None:
       
        for bodies in self.productions.values():
            for body in bodies:
                for symbol in body:
                    if symbol not in self.non_terminals:
                        self.terminals.add(symbol)

  

    def is_terminal(self, symbol: str) -> bool:
        return symbol in self.terminals

    def is_non_terminal(self, symbol: str) -> bool:
        return symbol in self.non_terminals

    def get_productions(self, non_terminal: str) -> list[list[str]]:
       
        return self.productions.get(non_terminal, [])

    def get_all_productions(self) -> list[Production]:
        """Retorna todas las producciones como objetos Production."""
        return [
            Production(head, bodies)
            for head, bodies in self.productions.items()
        ]

   
    def __str__(self) -> str:
        lines = [f"Símbolo inicial: {self.start_symbol}"]
        lines.append(f"No terminales: {', '.join(sorted(self.non_terminals))}")
        lines.append(f"Terminales: {', '.join(sorted(self.terminals))}")
        lines.append("Producciones:")
        for head, bodies in self.productions.items():
            bodies_str = " | ".join(" ".join(b) for b in bodies)
            lines.append(f"  {head} -> {bodies_str}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Grammar(start='{self.start_symbol}', rules={len(self.productions)})"

if __name__ == "__main__":
    # Gramática del profe: expresiones infijas
    texto_gramatica = """
    E -> E + T | E - T | T
    T -> T * F | T / F | F
    F -> ( E ) | identifier | número
    """

    g = Grammar()
    g.parse_from_string(texto_gramatica)
    print(g)
    print()
    print("Producciones de E :", g.get_productions("E"))
    print("Producciones de T :", g.get_productions("T"))
    print("Producciones de F :", g.get_productions("F"))
    print()
    print("¿'identifier' es terminal? :", g.is_terminal("identifier"))
    print("¿'número' es terminal?     :", g.is_terminal("número"))
    print("¿'+'  es terminal?         :", g.is_terminal("+"))
    print("¿'E'  es no-terminal?      :", g.is_non_terminal("E"))
    print()
    print("Símbolo inicial:", g.start_symbol)
    print("Todas las producciones:")
    for p in g.get_all_productions():
        print(" ", p)
