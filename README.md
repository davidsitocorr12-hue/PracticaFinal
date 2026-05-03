Generador de Árboles Sintácticos — Práctica Final
ST0244 - Lenguajes de Programación y Paradigmas de Computación  
---
Integrantes
DAVID MONCADA CORREA
Lenguaje y herramientas
Item	Detalle
Lenguaje	Python 3.11+
IDE	VS Code / PyCharm
Librerías principales	`nltk`, `matplotlib`, `tkinter`
---
Descripción
Aplicación con interfaz gráfica que, dada una gramática libre de contexto (CFG) en formato BNF y una expresión objetivo, genera:
Derivación paso a paso — izquierda o derecha, según selección del usuario.
Árbol de derivación — representación visual de todas las expansiones.
AST (Árbol de Sintaxis Abstracta) — versión simplificada que elimina nodos redundantes.
---
Estructura del proyecto
```
practica3/
├── main.py                  # Punto de entrada
├── grammar.py               # Clase Grammar — parsea reglas BNF
├── derivation_engine.py     # Clase DerivationEngine — derivación izq/der
├── parse_tree_builder.py    # Clase ParseTreeBuilder — árbol de derivación
├── ast_builder.py           # Clase ASTBuilder — AST simplificado
├── main_window.py           # Clase MainWindow — interfaz gráfica (tkinter)
├── requirements.txt
└── README.md
```
---
Cómo correr el proyecto
1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/practica3-arboles.git
cd practica3-arboles
```
2. Instalar dependencias
```bash
pip install -r requirements.txt
```
3. Ejecutar
```bash
python main.py
```
---
Gramática de ejemplo (expresiones infijas)
```
E -> E + T | E - T | T
T -> T * F | T / F | F
F -> ( E ) | identifier | número
```
Expresiones de prueba
```
identifier + identifier
identifier * número
identifier + número * identifier
identifier - número + identifier
```
> **Nota:** los tokens deben separarse con espacios. Los paréntesis también son tokens: `( identifier + número )`.
---
Arquitectura OOP
```
MainWindow
    │
    ├── Grammar              (parsea BNF)
    ├── DerivationEngine     (usa NLTK ChartParser)
    │       └── deriva izquierda / derecha
    ├── ParseTreeBuilder     (construye TreeNode desde NLTK)
    │       └── TreeNode
    └── ASTBuilder           (simplifica TreeNode → ASTNode)
            └── ASTNode
```
---
Paradigma aplicado
El proyecto aplica Programación Orientada a Objetos con:
Encapsulamiento — cada clase oculta su implementación interna.
Separación de responsabilidades — lógica, dominio y presentación en clases distintas.
Composición — `MainWindow` compone los motores del dominio sin heredar de ellos.
Polimorfismo — `TreeDrawer` dibuja tanto `TreeNode` como `ASTNode` con la misma interfaz.
