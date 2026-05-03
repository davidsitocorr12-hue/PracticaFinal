
import nltk
from nltk import CFG, ChartParser
from grammar import Grammar


class TreeNode:
   
    def __init__(self, symbol: str, is_terminal: bool = False):
        self.symbol = symbol
        self.children: list["TreeNode"] = []
        self.is_terminal = is_terminal

    def add_child(self, node: "TreeNode") -> None:
        self.children.append(node)

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __repr__(self) -> str:
        return f"TreeNode('{self.symbol}', terminal={self.is_terminal}, children={len(self.children)})"


class ParseTreeBuilder:


    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self._nltk_grammar = self._build_nltk_grammar(grammar)
        self._parser = ChartParser(self._nltk_grammar)

    
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

   

    def build(self, tokens: list) -> TreeNode:
        """
        Construye el árbol de derivación para la lista de tokens dada.

        Args:
            tokens: Lista de tokens terminales. Ej: ["identifier", "+", "identifier"]

        Returns:
            Nodo raíz (TreeNode) del árbol de derivación completo.

        Raises:
            ValueError: Si la expresión no pertenece al lenguaje.
        """
        nltk_tree = self._get_nltk_tree(tokens)
        return self._convert(nltk_tree)

    def _get_nltk_tree(self, tokens: list):
        """Obtiene el primer árbol de parseo de NLTK ChartParser."""
        try:
            trees = list(self._parser.parse(tokens))
        except Exception as exc:
            raise ValueError(f"Error al parsear '{' '.join(tokens)}': {exc}") from exc

        if not trees:
            raise ValueError(
                f"La expresión '{' '.join(tokens)}' no pertenece al lenguaje.\n"
                "Verifica los tokens y las reglas de la gramática."
            )
        return trees[0]

  

    def _convert(self, nltk_node) -> TreeNode:

        if isinstance(nltk_node, nltk.Tree):
            node = TreeNode(
                symbol=nltk_node.label(),
                is_terminal=False
            )
            for child in nltk_node:
                node.add_child(self._convert(child))
            return node
        else:
            # Es una hoja terminal (string)
            return TreeNode(symbol=str(nltk_node), is_terminal=True)

    

    def to_text(self, node: TreeNode, prefix: str = "", is_last: bool = True) -> str:
       
        connector = "└── " if is_last else "├── "
        line = prefix + (connector if prefix else "") + node.symbol + "\n"

        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_child_last = (i == len(node.children) - 1)
            line += self.to_text(child, child_prefix, is_child_last)

        return line

    def to_bracket_notation(self, node: TreeNode) -> str:
       
        if node.is_leaf():
            return node.symbol
        children_str = " ".join(self.to_bracket_notation(c) for c in node.children)
        return f"[{node.symbol} {children_str}]"


    def height(self, node: TreeNode) -> int:
        """Calcula la altura del árbol."""
        if node.is_leaf():
            return 0
        return 1 + max(self.height(c) for c in node.children)

    def count_nodes(self, node: TreeNode) -> int:
        """Cuenta el total de nodos del árbol."""
        return 1 + sum(self.count_nodes(c) for c in node.children)

    def get_leaves(self, node: TreeNode) -> list:
        """Retorna los nodos hoja (terminales) en orden izquierda→derecha."""
        if node.is_leaf():
            return [node]
        leaves = []
        for child in node.children:
            leaves.extend(self.get_leaves(child))
        return leaves

if __name__ == "__main__":
    from grammar import Grammar

    g = Grammar()
    g.parse_from_string("""
    E -> E + T | E - T | T
    T -> T * F | T / F | F
    F -> ( E ) | identifier | número
    """)

    builder = ParseTreeBuilder(g)

    tests = [
        ["identifier", "+", "identifier"],
        ["identifier", "*", "número"],
        ["identifier", "+", "número", "*", "identifier"],
    ]

    for tokens in tests:
        print("=" * 55)
        print(f"Expresión: {' '.join(tokens)}")
        root = builder.build(tokens)

        print("\nÁrbol de derivación (texto):")
        print(builder.to_text(root))

        print(f"Notación corchetes: {builder.to_bracket_notation(root)}")
        print(f"Altura del árbol  : {builder.height(root)}")
        print(f"Total de nodos    : {builder.count_nodes(root)}")
        hojas = builder.get_leaves(root)
        print(f"Hojas (terminales): {[h.symbol for h in hojas]}")
