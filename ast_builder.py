

from parse_tree_builder import TreeNode


class ASTNode:
  
    def __init__(self, value: str, node_type: str = "operand"):
        self.value = value
        self.node_type = node_type
        self.children: list["ASTNode"] = []

    def add_child(self, node: "ASTNode") -> None:
        self.children.append(node)

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __repr__(self) -> str:
        return f"ASTNode('{self.value}', type='{self.node_type}', children={len(self.children)})"


class ASTBuilder:
  

    # Símbolos que se eliminan del AST (no aportan semántica)
    PUNCTUATION = {"(", ")", ",", ";"}

    # Operadores reconocidos
    OPERATORS = {"+", "-", "*", "/"}

    def __init__(self, grammar):
        self.grammar = grammar

   
    def build(self, parse_tree_root: TreeNode) -> ASTNode:
       
        return self._simplify(parse_tree_root)

  
    def _simplify(self, node: TreeNode) -> ASTNode | None:
      
        # -- Caso hoja terminal --
        if node.is_leaf():
            return self._handle_terminal(node)

        # -- Caso nodo con hijos: recopilar hijos relevantes --
        simplified_children = []
        operators_found = []

        for child in node.children:
            if child.is_leaf():
                sym = child.symbol
                if sym in self.PUNCTUATION:
                    continue  # descartar paréntesis, etc.
                if sym in self.OPERATORS:
                    operators_found.append(sym)
                    continue  # el operador se usará como nodo raíz
                # Terminal operando → convertir
                ast_child = self._handle_terminal(child)
                if ast_child:
                    simplified_children.append(ast_child)
            else:
                # No-terminal → simplificar recursivamente
                ast_child = self._simplify(child)
                if ast_child:
                    simplified_children.append(ast_child)

        # -- Regla 1: nodo con operador binario A op B --
        if operators_found:
            op = operators_found[0]  # solo uno por producción
            op_node = ASTNode(value=op, node_type="operator")
            for child in simplified_children:
                op_node.add_child(child)
            return op_node

        # -- Regla 2: nodo con un solo hijo relevante → colapsar --
        if len(simplified_children) == 1:
            return simplified_children[0]

        # -- Regla 3: nodo con múltiples hijos sin operador explícito --
        # (caso raro, por ejemplo F -> ( E )) — retorna el hijo principal
        if len(simplified_children) > 1:
            # Crear un nodo genérico con el símbolo del no-terminal
            parent = ASTNode(value=node.symbol, node_type="non-terminal")
            for child in simplified_children:
                parent.add_child(child)
            return parent

        return None

    def _handle_terminal(self, node: TreeNode) -> ASTNode | None:
      
        sym = node.symbol

        if sym in self.PUNCTUATION:
            return None

        if sym in self.OPERATORS:
            return ASTNode(value=sym, node_type="operator")

        if sym == "identifier":
            return ASTNode(value=sym, node_type="identifier")

        if sym == "número":
            return ASTNode(value=sym, node_type="número")

        # Cualquier otro terminal
        return ASTNode(value=sym, node_type="terminal")


    def to_text(self, node: ASTNode, prefix: str = "", is_last: bool = True) -> str:
    
        connector = "└── " if is_last else "├── "
        label = f"{node.value}  [{node.node_type}]" if node.node_type == "operator" else node.value
        line = prefix + (connector if prefix else "") + label + "\n"

        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            is_child_last = (i == len(node.children) - 1)
            line += self.to_text(child, child_prefix, is_child_last)

        return line

    def to_bracket_notation(self, node: ASTNode) -> str:
       
        if node.is_leaf():
            return node.value
        children_str = " ".join(self.to_bracket_notation(c) for c in node.children)
        return f"[{node.value} {children_str}]"

    def height(self, node: ASTNode) -> int:
        """Altura del AST."""
        if node.is_leaf():
            return 0
        return 1 + max(self.height(c) for c in node.children)

    def count_nodes(self, node: ASTNode) -> int:
        """Total de nodos del AST."""
        return 1 + sum(self.count_nodes(c) for c in node.children)

    def get_operators(self, node: ASTNode) -> list:
        """Retorna todos los operadores del AST en orden preorden."""
        result = []
        if node.node_type == "operator":
            result.append(node.value)
        for child in node.children:
            result.extend(self.get_operators(child))
        return result

    def get_operands(self, node: ASTNode) -> list:
        """Retorna todos los operandos (hojas) del AST."""
        if node.is_leaf():
            return [node.value]
        result = []
        for child in node.children:
            result.extend(self.get_operands(child))
        return result

if __name__ == "__main__":
    from grammar import Grammar
    from parse_tree_builder import ParseTreeBuilder

    g = Grammar()
    g.parse_from_string("""
    E -> E + T | E - T | T
    T -> T * F | T / F | F
    F -> ( E ) | identifier | número
    """)

    tree_builder = ParseTreeBuilder(g)
    ast_builder = ASTBuilder(g)

    tests = [
        ["identifier", "+", "identifier"],
        ["identifier", "*", "número"],
        ["identifier", "+", "número", "*", "identifier"],
        ["identifier", "-", "número", "+", "identifier"],
    ]

    for tokens in tests:
        print("=" * 55)
        print(f"Expresión: {' '.join(tokens)}")

        parse_root = tree_builder.build(tokens)
        ast_root = ast_builder.build(parse_root)

        print("\nÁrbol de derivación:")
        print(tree_builder.to_text(parse_root))

        print("AST (simplificado):")
        print(ast_builder.to_text(ast_root))

        print(f"Notación AST  : {ast_builder.to_bracket_notation(ast_root)}")
        print(f"Operadores    : {ast_builder.get_operators(ast_root)}")
        print(f"Operandos     : {ast_builder.get_operands(ast_root)}")
        print(f"Altura AST    : {ast_builder.height(ast_root)}")
        print(f"Nodos AST     : {ast_builder.count_nodes(ast_root)}")
        print(f"Nodos árbol   : {tree_builder.count_nodes(parse_root)}")
