"""
main_window.py
Clase MainWindow: interfaz gráfica principal del generador de árboles sintácticos.

Integra los módulos:
  - Grammar          → parsea las reglas BNF
  - DerivationEngine → genera derivación izquierda / derecha
  - ParseTreeBuilder → construye el árbol de derivación
  - ASTBuilder       → simplifica el árbol en un AST

Tecnología: tkinter + matplotlib (embebido en tkinter) + NLTK

Autor: [Tu nombre]
Curso: ST0244 - Lenguajes de Programación y Paradigmas de Computación
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import nltk

from grammar import Grammar
from derivation_engine import DerivationEngine
from parse_tree_builder import ParseTreeBuilder, TreeNode
from ast_builder import ASTBuilder, ASTNode
from lexer import Lexer, LexerError


# ──────────────────────────────────────────────────────────────────────────────
# Utilidad: dibujador de árboles con matplotlib
# ──────────────────────────────────────────────────────────────────────────────

class TreeDrawer:
    """
    Dibuja un árbol (TreeNode o ASTNode) sobre un Axes de matplotlib.

    Calcula posiciones con un layout de árbol binario generalizado:
      - Asigna a cada hoja una posición x equidistante.
      - Los nodos internos se centran sobre sus hijos.
      - El nivel y es proporcional a la profundidad.
    """

    NODE_RADIUS = 0.35
    LEVEL_HEIGHT = 1.4
    FONT_SIZE = 9

    def draw(self, ax, root, is_ast: bool = False) -> None:
        """
        Dibuja el árbol en el Axes dado.

        Args:
            ax:     Axes de matplotlib donde se dibuja.
            root:   Nodo raíz (TreeNode o ASTNode).
            is_ast: True si es un AST (usa colores distintos).
        """
        ax.clear()
        ax.set_aspect("equal")
        ax.axis("off")

        # Calcular posiciones
        positions = {}
        self._assign_positions(root, positions, depth=0, counter=[0])

        # Escalar el eje
        if positions:
            xs = [p[0] for p in positions.values()]
            ys = [p[1] for p in positions.values()]
            margin = 1.0
            ax.set_xlim(min(xs) - margin, max(xs) + margin)
            ax.set_ylim(min(ys) - margin, max(ys) + margin)

        # Dibujar aristas primero (quedan detrás de los nodos)
        self._draw_edges(ax, root, positions)

        # Dibujar nodos encima
        self._draw_nodes(ax, root, positions, is_ast)

    def _assign_positions(self, node, positions: dict, depth: int, counter: list) -> float:
        """
        Asigna coordenadas (x, y) a cada nodo.
        Las hojas obtienen posiciones x consecutivas; los nodos internos
        se centran sobre el rango de sus hijos.

        Returns:
            Centro x del subárbol de este nodo.
        """
        children = self._get_children(node)

        if not children:
            # Hoja: posición x = siguiente contador
            x = float(counter[0])
            counter[0] += 1.2
            y = -depth * self.LEVEL_HEIGHT
            positions[id(node)] = (x, y)
            return x

        # Nodo interno: calcular rango de hijos
        child_xs = [self._assign_positions(c, positions, depth + 1, counter) for c in children]
        x = (child_xs[0] + child_xs[-1]) / 2.0
        y = -depth * self.LEVEL_HEIGHT
        positions[id(node)] = (x, y)
        return x

    def _draw_edges(self, ax, node, positions: dict) -> None:
        """Dibuja las aristas del árbol recursivamente."""
        children = self._get_children(node)
        if id(node) not in positions:
            return
        x1, y1 = positions[id(node)]
        for child in children:
            if id(child) in positions:
                x2, y2 = positions[id(child)]
                ax.plot([x1, x2], [y1, y2], color="#9E9E9E", linewidth=1.2, zorder=1)
            self._draw_edges(ax, child, positions)

    def _draw_nodes(self, ax, node, positions: dict, is_ast: bool) -> None:
        """Dibuja los nodos del árbol recursivamente."""
        if id(node) not in positions:
            return

        x, y = positions[id(node)]
        label, is_terminal, is_operator = self._node_info(node)

        # Color según tipo
        if is_ast:
            if is_operator:
                facecolor, edgecolor, textcolor = "#4A90D9", "#2C5F8A", "white"
            else:
                facecolor, edgecolor, textcolor = "#E8F4E8", "#3A7D3A", "#1A4A1A"
        else:
            if is_terminal:
                facecolor, edgecolor, textcolor = "#FFF3CD", "#C8860A", "#5D3A00"
            else:
                facecolor, edgecolor, textcolor = "#D6EAF8", "#1A6BA0", "#0D3B5E"

        circle = plt.Circle(
            (x, y), self.NODE_RADIUS,
            facecolor=facecolor, edgecolor=edgecolor,
            linewidth=1.5, zorder=2
        )
        ax.add_patch(circle)
        ax.text(
            x, y, label,
            ha="center", va="center",
            fontsize=self.FONT_SIZE, fontweight="bold",
            color=textcolor, zorder=3
        )

        for child in self._get_children(node):
            self._draw_nodes(ax, child, positions, is_ast)

    # ------------------------------------------------------------------
    # Helpers polimórficos (funcionan con TreeNode y ASTNode)
    # ------------------------------------------------------------------

    def _get_children(self, node) -> list:
        return node.children if hasattr(node, "children") else []

    def _node_info(self, node) -> tuple:
        """Retorna (label, is_terminal, is_operator) según el tipo de nodo."""
        if isinstance(node, TreeNode):
            return node.symbol, node.is_terminal, False
        if isinstance(node, ASTNode):
            return node.value, node.is_leaf(), node.node_type == "operator"
        return str(node), True, False


# ──────────────────────────────────────────────────────────────────────────────
# Ventana principal
# ──────────────────────────────────────────────────────────────────────────────

class MainWindow:
    """
    Ventana principal de la aplicación.

    Layout:
    ┌─────────────────────────────────────────────────────┐
    │  Panel izquierdo         │  Panel derecho (árboles) │
    │  ├─ Gramática (textarea) │  ├─ Árbol de derivación  │
    │  ├─ Expresión (entry)    │  └─ AST                  │
    │  ├─ Opciones derivación  │                          │
    │  ├─ Botón Generar        │                          │
    │  └─ Derivación (texto)   │                          │
    └─────────────────────────────────────────────────────┘
    """

    GRAMMAR_DEFAULT = (
        "E -> E + T | E - T | T\n"
        "T -> T * F | T / F | F\n"
        "F -> ( E ) | identifier | número"
    )
    EXPRESSION_DEFAULT = "5 + 2 * x"
    WINDOW_TITLE = "Generador de Árboles Sintácticos — ST0244 EAFIT"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry("1280x780")
        self.root.minsize(900, 600)
        self.root.configure(bg="#F5F6FA")

        # Objetos del dominio (se crean al presionar Generar)
        self.grammar: Grammar | None = None
        self.engine: DerivationEngine | None = None
        self.tree_builder: ParseTreeBuilder | None = None
        self.ast_builder: ASTBuilder | None = None

        self._build_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Construye todos los widgets de la ventana."""
        # Marco raíz con dos columnas
        main_frame = tk.Frame(self.root, bg="#F5F6FA")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)

        self._build_left_panel(main_frame)
        self._build_right_panel(main_frame)

    def _build_left_panel(self, parent) -> None:
        """Panel izquierdo: gramática, expresión, controles, derivación."""
        left = tk.Frame(parent, bg="#F5F6FA")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(3, weight=1)  # el área de derivación crece

        # ── Gramática ──
        tk.Label(left, text="Gramática (formato BNF):",
                 bg="#F5F6FA", font=("Helvetica", 10, "bold"),
                 anchor="w").grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self.grammar_text = scrolledtext.ScrolledText(
            left, height=6, font=("Courier", 10),
            relief="solid", borderwidth=1, wrap=tk.WORD
        )
        self.grammar_text.insert("1.0", self.GRAMMAR_DEFAULT)
        self.grammar_text.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # ── Expresión ──
        tk.Label(left, text="Expresión (puedes escribir: 5 + 2 * x, a - b, etc.):",
                 bg="#F5F6FA", font=("Helvetica", 10, "bold"),
                 anchor="w").grid(row=2, column=0, sticky="ew", pady=(0, 4))

        expr_frame = tk.Frame(left, bg="#F5F6FA")
        expr_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        expr_frame.columnconfigure(0, weight=1)

        self.expr_entry = tk.Entry(
            expr_frame, font=("Courier", 11),
            relief="solid", borderwidth=1
        )
        self.expr_entry.insert(0, self.EXPRESSION_DEFAULT)
        self.expr_entry.grid(row=0, column=0, sticky="ew", ipady=4)

        # Label que muestra cómo se convierten los tokens
        self.token_label = tk.Label(
            left, text="",
            bg="#F5F6FA", font=("Courier", 9),
            fg="#555555", anchor="w", wraplength=380, justify="left"
        )
        self.token_label.grid(row=4, column=0, sticky="ew", pady=(0, 6))

        # ── Opciones de derivación ──
        opts_frame = tk.LabelFrame(
            left, text="  Opciones de derivación  ",
            bg="#F5F6FA", font=("Helvetica", 10, "bold"),
            relief="solid", borderwidth=1, padx=10, pady=6
        )
        opts_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        self.derivation_var = tk.StringVar(value="left")
        tk.Radiobutton(
            opts_frame, text="Derivación por la Izquierda",
            variable=self.derivation_var, value="left",
            bg="#F5F6FA", font=("Helvetica", 10),
            activebackground="#F5F6FA"
        ).pack(anchor="w")
        tk.Radiobutton(
            opts_frame, text="Derivación por la Derecha",
            variable=self.derivation_var, value="right",
            bg="#F5F6FA", font=("Helvetica", 10),
            activebackground="#F5F6FA"
        ).pack(anchor="w")

        # ── Botón generar ──
        self.btn_generate = tk.Button(
            left, text="⚙  Generar Derivación",
            command=self._on_generate,
            font=("Helvetica", 11, "bold"),
            relief="flat", cursor="hand2",
            padx=16, pady=8
        )
        self.btn_generate.grid(row=6, column=0, sticky="ew", pady=(0, 12))

        # ── Área de derivación paso a paso ──
        tk.Label(left, text="Derivación paso a paso:",
                 bg="#F5F6FA", font=("Helvetica", 10, "bold"),
                 anchor="w").grid(row=7, column=0, sticky="ew", pady=(0, 4))

        self.derivation_text = scrolledtext.ScrolledText(
            left, font=("Courier", 10),
            relief="solid", borderwidth=1,
            state=tk.DISABLED, wrap=tk.NONE
        )
        self.derivation_text.grid(row=8, column=0, sticky="nsew")
        left.rowconfigure(8, weight=1)

    def _build_right_panel(self, parent) -> None:
        """Panel derecho: árbol de derivación y AST con pestañas."""
        right = tk.Frame(parent, bg="#F5F6FA")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(right)
        notebook.grid(row=0, column=0, sticky="nsew")

        # Pestaña 1: Árbol de derivación
        tab_tree = tk.Frame(notebook, bg="white")
        notebook.add(tab_tree, text="  Árbol de derivación  ")
        tab_tree.rowconfigure(0, weight=1)
        tab_tree.columnconfigure(0, weight=1)

        self.fig_tree, self.ax_tree = plt.subplots(figsize=(6, 5))
        self.fig_tree.patch.set_facecolor("white")
        self.canvas_tree = FigureCanvasTkAgg(self.fig_tree, master=tab_tree)
        self.canvas_tree.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._show_empty_plot(self.ax_tree, self.canvas_tree, "El árbol de derivación aparecerá aquí")

        # Pestaña 2: AST
        tab_ast = tk.Frame(notebook, bg="white")
        notebook.add(tab_ast, text="  AST (árbol simplificado)  ")
        tab_ast.rowconfigure(0, weight=1)
        tab_ast.columnconfigure(0, weight=1)

        self.fig_ast, self.ax_ast = plt.subplots(figsize=(6, 5))
        self.fig_ast.patch.set_facecolor("white")
        self.canvas_ast = FigureCanvasTkAgg(self.fig_ast, master=tab_ast)
        self.canvas_ast.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._show_empty_plot(self.ax_ast, self.canvas_ast, "El AST aparecerá aquí")

        # Leyenda
        legend_frame = tk.Frame(right, bg="#F5F6FA")
        legend_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        tk.Label(legend_frame, text="■ No-terminal  ■ Terminal  ■ Operador AST  ■ Operando AST",
                 bg="#F5F6FA", font=("Helvetica", 8),
                 fg="#666666").pack()

    # ------------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        """Aplica colores y estilos a los widgets."""
        self.btn_generate.configure(bg="#2563EB", fg="white",
                                    activebackground="#1D4ED8", activeforeground="white")
        self.derivation_text.configure(bg="#F8F9FA", fg="#1A1A2E")
        self.grammar_text.configure(bg="#FAFAFA", fg="#1A1A2E")
        self.expr_entry.configure(bg="#FAFAFA", fg="#1A1A2E")

        style = ttk.Style()
        style.configure("TNotebook", background="#F5F6FA")
        style.configure("TNotebook.Tab", font=("Helvetica", 10, "bold"), padding=[10, 4])

    # ------------------------------------------------------------------
    # Lógica principal: evento Generar
    # ------------------------------------------------------------------

    def _on_generate(self) -> None:
        """
        Manejador del botón 'Generar Derivación'.
        Coordina todos los módulos del dominio y actualiza la UI.
        """
        grammar_text = self.grammar_text.get("1.0", tk.END).strip()
        expression_text = self.expr_entry.get().strip()
        direction = self.derivation_var.get()

        # 1. Validar entradas
        if not grammar_text:
            messagebox.showerror("Error", "Por favor ingresa la gramática.")
            return
        if not expression_text:
            messagebox.showerror("Error", "Por favor ingresa la expresión.")
            return

        # 2. Tokenizar la expresión con el Lexer
        try:
            lexer = Lexer()
            tokens, descripciones = lexer.tokenize(expression_text)
            # Mostrar la conversión al usuario
            self.token_label.config(
                text="Tokens: " + "  |  ".join(descripciones),
                fg="#0A6E0A"
            )
        except LexerError as e:
            self.token_label.config(text=f"Error: {e}", fg="#CC0000")
            messagebox.showerror("Error en la expresión", str(e))
            return

        # 3. Parsear gramática
        try:
            self.grammar = Grammar()
            self.grammar.parse_from_string(grammar_text)
        except ValueError as e:
            messagebox.showerror("Error en la gramática", str(e))
            return

        # 4. Construir motores
        try:
            self.engine = DerivationEngine(self.grammar)
            self.tree_builder = ParseTreeBuilder(self.grammar)
            self.ast_builder = ASTBuilder(self.grammar)
        except Exception as e:
            messagebox.showerror("Error al construir el motor", str(e))
            return

        # 5. Generar derivación
        try:
            if direction == "left":
                steps = self.engine.derive_left(tokens)
            else:
                steps = self.engine.derive_right(tokens)
        except ValueError as e:
            messagebox.showerror("Error en la derivación", str(e))
            return

        # 6. Mostrar derivación en texto con valores reales
        derivation_str = self._format_derivation_real(
            steps, self.grammar.start_symbol, descripciones, expression_text
        )
        self._set_derivation_text(derivation_str)

        # 7. Construir y dibujar árbol de derivación con valores reales
        try:
            parse_root = self.tree_builder.build(tokens)
            self._replace_leaves(parse_root, descripciones)
            drawer = TreeDrawer()
            drawer.draw(self.ax_tree, parse_root, is_ast=False)
            self.canvas_tree.draw()
        except Exception as e:
            self._show_empty_plot(self.ax_tree, self.canvas_tree, f"Error: {e}")

        # 8. Construir y dibujar AST con valores reales
        try:
            ast_root = self.ast_builder.build(parse_root)
            drawer = TreeDrawer()
            drawer.draw(self.ax_ast, ast_root, is_ast=True)
            self.canvas_ast.draw()
        except Exception as e:
            self._show_empty_plot(self.ax_ast, self.canvas_ast, f"Error: {e}")

    # ------------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------------

    def _replace_leaves(self, node, descripciones: list) -> None:
        """
        Recorre el árbol de derivación en orden izquierda→derecha y reemplaza
        las hojas 'número' e 'identifier' por los valores reales del usuario.

        Por ejemplo: hoja 'número' → '5', hoja 'identifier' → 'x'

        Args:
            node:         Nodo raíz del árbol (TreeNode).
            descripciones: Lista de descripciones del lexer, ej ["5→número", "+", "x→identifier"]
        """
        # Extraer valores reales en orden de aparición
        nums = [d.split("→")[0] for d in descripciones if "→número" in d]
        ids  = [d.split("→")[0] for d in descripciones if "→identifier" in d]

        counters = {"número": 0, "identifier": 0}

        def _walk(n):
            if n.is_leaf():
                if n.symbol == "número" and counters["número"] < len(nums):
                    n.symbol = nums[counters["número"]]
                    counters["número"] += 1
                elif n.symbol == "identifier" and counters["identifier"] < len(ids):
                    n.symbol = ids[counters["identifier"]]
                    counters["identifier"] += 1
            else:
                for child in n.children:
                    _walk(child)

        _walk(node)

    def _format_derivation_real(
        self, steps, start_symbol: str, descripciones: list, expression_text: str
    ) -> str:
        """
        Formatea la derivación reemplazando 'número' e 'identifier'
        por los valores reales que el usuario escribió.

        Por ejemplo, si el usuario escribió "5 + 2 * x":
          número → 5, número → 2, identifier → x

        Cada aparición de número/identifier se reemplaza en orden
        de izquierda a derecha, respetando el orden de los tokens.
        """
        # Extraer valores reales en orden: "5→número" → "5", "x→identifier" → "x"
        real_values = []
        for d in descripciones:
            if "→" in d:
                valor = d.split("→")[0]
                real_values.append(valor)
            else:
                real_values.append(d)  # operadores: +, -, *, /

        # Función que reemplaza tokens genéricos por valores reales en una forma sentencial
        def reemplazar(forma: list) -> str:
            resultado = []
            # Contadores independientes para cada tipo de token genérico
            idx_num = 0
            idx_id  = 0

            # Construir lista de valores reales por tipo
            nums = [v for d, v in zip(descripciones, real_values) if "número" in d]
            ids  = [v for d, v in zip(descripciones, real_values) if "identifier" in d]

            for sym in forma:
                if sym == "número":
                    resultado.append(nums[idx_num] if idx_num < len(nums) else sym)
                    idx_num += 1
                elif sym == "identifier":
                    resultado.append(ids[idx_id] if idx_id < len(ids) else sym)
                    idx_id += 1
                else:
                    resultado.append(sym)
            return " ".join(resultado)

        # Construir la derivación con valores reales
        lines = [start_symbol]
        for step in steps:
            lines.append(f"=> {reemplazar(step.sentential_form)}")

        return "\n".join(lines)

    def _set_derivation_text(self, text: str) -> None:
        """Actualiza el área de texto con los pasos de derivación."""
        self.derivation_text.configure(state=tk.NORMAL)
        self.derivation_text.delete("1.0", tk.END)
        self.derivation_text.insert("1.0", text)
        self.derivation_text.configure(state=tk.DISABLED)

    def _show_empty_plot(self, ax, canvas, message: str) -> None:
        """Muestra un mensaje en un plot vacío."""
        ax.clear()
        ax.axis("off")
        ax.text(
            0.5, 0.5, message,
            ha="center", va="center",
            fontsize=11, color="#AAAAAA",
            transform=ax.transAxes
        )
        canvas.draw()

    # ------------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Inicia el loop principal de tkinter."""
        self.root.mainloop()


# ──────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = MainWindow()
    app.run()
