"""
derivation_engine.py
Clase DerivationEngine: derivaciones izquierda y derecha usando NLTK ChartParser.

Autor: [Tu nombre]
Curso: ST0244 - Lenguajes de Programación y Paradigmas de Computación
"""

import nltk
from nltk import CFG, ChartParser
from grammar import Grammar


class DerivationStep:
    """Un paso individual de la derivación."""

    def __init__(self, sentential_form: list, expanded_symbol: str,
                 production_used: list, position: int):
        self.sentential_form = sentential_form
        self.expanded_symbol = expanded_symbol
        self.production_used = production_used
        self.position = position

    def __str__(self):
        return " ".join(self.sentential_form)

    def to_arrow_str(self):
        return f"=> {' '.join(self.sentential_form)}"


class DerivationEngine:
    """
    Motor de derivación izquierda y derecha para gramáticas CFG.

    Usa NLTK ChartParser para obtener el árbol de parseo y luego
    recorre ese árbol para reconstruir los pasos de derivación.

    Algoritmo:
      - Derivación IZQUIERDA: preorden del árbol (raíz → hijos izq→der).
        Siempre se busca y expande el no-terminal más a la IZQUIERDA.
      - Derivación DERECHA: preorden con hijos der→izq (right-first preorder).
        Siempre se busca y expande el no-terminal más a la DERECHA.
    """

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self._nltk_grammar = self._build_nltk_grammar(grammar)
        self._parser = ChartParser(self._nltk_grammar)

    # ------------------------------------------------------------------
    # Construcción gramática NLTK
    # ------------------------------------------------------------------

    def _build_nltk_grammar(self, grammar: Grammar) -> CFG:
        """Convierte nuestro Grammar al formato CFG de NLTK."""
        lines = []
        ordered = [grammar.start_symbol] + [
            nt for nt in grammar.productions if nt != grammar.start_symbol
        ]
        for nt in ordered:
            for body in grammar.productions[nt]:
                rhs = " ".join(
                    f"'{s}'" if grammar.is_terminal(s) else s
                    for s in body
                )
                lines.append(f"{nt} -> {rhs}")
        return CFG.fromstring("\n".join(lines))

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def derive_left(self, target_tokens: list) -> list:
        """
        Derivación más a la izquierda (leftmost derivation).

        En cada paso se expande el no-terminal más a la izquierda
        de la forma sentencial actual.

        Args:
            target_tokens: Lista de tokens terminales de la expresión.
                           Ej: ["identifier", "+", "identifier"]

        Returns:
            Lista de DerivationStep, uno por cada expansión realizada.

        Raises:
            ValueError: Si la expresión no pertenece al lenguaje de la gramática.
        """
        tree = self._parse_tree(target_tokens)
        productions = []
        self._preorder(tree, productions)
        return self._simulate(productions, leftmost=True)

    def derive_right(self, target_tokens: list) -> list:
        """
        Derivación más a la derecha (rightmost derivation).

        En cada paso se expande el no-terminal más a la derecha
        de la forma sentencial actual.

        Args:
            target_tokens: Lista de tokens terminales de la expresión.

        Returns:
            Lista de DerivationStep, uno por cada expansión realizada.

        Raises:
            ValueError: Si la expresión no pertenece al lenguaje de la gramática.
        """
        tree = self._parse_tree(target_tokens)
        productions = []
        self._right_first_preorder(tree, productions)
        return self._simulate(productions, leftmost=False)

    # ------------------------------------------------------------------
    # Parseo NLTK
    # ------------------------------------------------------------------

    def _parse_tree(self, tokens: list):
        """Obtiene el primer árbol de parseo válido con NLTK ChartParser."""
        try:
            trees = list(self._parser.parse(tokens))
        except Exception as exc:
            raise ValueError(
                f"Error al parsear '{' '.join(tokens)}': {exc}"
            ) from exc

        if not trees:
            raise ValueError(
                f"La expresión '{' '.join(tokens)}' no pertenece al lenguaje.\n"
                "Verifica que los tokens y las reglas de la gramática sean correctos."
            )
        return trees[0]

    # ------------------------------------------------------------------
    # Recorridos del árbol
    # ------------------------------------------------------------------

    def _preorder(self, node, result: list):
        """
        Preorden izquierda→derecha: raíz, luego hijos de izq a der.
        Produce el orden de expansión para derivación izquierda.
        """
        if not isinstance(node, nltk.Tree):
            return
        head = node.label()
        body = [
            child.label() if isinstance(child, nltk.Tree) else child
            for child in node
        ]
        result.append((head, body))
        for child in node:
            self._preorder(child, result)

    def _right_first_preorder(self, node, result: list):
        """
        Preorden derecha→izquierda: raíz, luego hijos de der a izq.
        Produce el orden de expansión para derivación derecha.
        """
        if not isinstance(node, nltk.Tree):
            return
        head = node.label()
        body = [
            child.label() if isinstance(child, nltk.Tree) else child
            for child in node
        ]
        result.append((head, body))
        for child in reversed(list(node)):
            self._right_first_preorder(child, result)

    # ------------------------------------------------------------------
    # Simulación de la derivación
    # ------------------------------------------------------------------

    def _simulate(self, productions: list, leftmost: bool) -> list:
        """
        Aplica la secuencia de producciones sobre la forma sentencial
        inicial (símbolo de inicio) y genera los pasos de derivación.

        Args:
            productions: Lista de (cabeza, cuerpo) en el orden del recorrido.
            leftmost: True → busca el no-terminal más a la izquierda.
                      False → busca el no-terminal más a la derecha.

        Returns:
            Lista de DerivationStep.
        """
        current = [self.grammar.start_symbol]
        steps = []

        for head, body in productions:
            if leftmost:
                # Primer no-terminal igual a head
                pos = next(
                    (i for i, s in enumerate(current)
                     if s == head and self.grammar.is_non_terminal(s)),
                    None
                )
            else:
                # Último no-terminal igual a head
                pos = None
                for i in range(len(current) - 1, -1, -1):
                    if current[i] == head and self.grammar.is_non_terminal(current[i]):
                        pos = i
                        break

            if pos is None:
                continue

            new_form = current[:pos] + body + current[pos + 1:]
            steps.append(DerivationStep(
                sentential_form=new_form[:],
                expanded_symbol=head,
                production_used=body[:],
                position=pos,
            ))
            current = new_form

        return steps

    # ------------------------------------------------------------------
    # Formateo
    # ------------------------------------------------------------------

    def format_derivation(self, steps: list, start_symbol: str = None) -> str:
        """
        Formatea los pasos como texto legible con flechas '=>'.

        Ejemplo de salida:
            E
            => E + T
            => T + T
            => F + T
            => identifier + T
            => identifier + F
            => identifier + identifier
        """
        start = start_symbol or self.grammar.start_symbol
        lines = [start]
        for step in steps:
            lines.append(step.to_arrow_str())
        return "\n".join(lines)


# ------------------------------------------------------------------
# Prueba rápida (ejecuta: python derivation_engine.py)
# ------------------------------------------------------------------
if __name__ == "__main__":
    from grammar import Grammar

    g = Grammar()
    g.parse_from_string("""
    E -> E + T | E - T | T
    T -> T * F | T / F | F
    F -> ( E ) | identifier | número
    """)

    engine = DerivationEngine(g)

    tests = [
        ["identifier", "+", "identifier"],
        ["identifier", "*", "número"],
        ["identifier", "+", "número", "*", "identifier"],
    ]

    for expr in tests:
        print("=" * 55)
        print(f"Expresión: {' '.join(expr)}")

        print("\n--- Derivación IZQUIERDA ---")
        try:
            steps = engine.derive_left(expr)
            print(engine.format_derivation(steps))
            print(f"Pasos: {len(steps)}")
        except ValueError as e:
            print(f"Error: {e}")

        print("\n--- Derivación DERECHA ---")
        try:
            steps = engine.derive_right(expr)
            print(engine.format_derivation(steps))
            print(f"Pasos: {len(steps)}")
        except ValueError as e:
            print(f"Error: {e}")
