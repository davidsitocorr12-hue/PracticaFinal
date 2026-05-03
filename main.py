"""
main.py
Punto de entrada de la aplicación.

Cómo correr:
    python main.py

Requisitos:
    pip install nltk matplotlib

Autor: [Tu nombre]
Curso: ST0244 - Lenguajes de Programación y Paradigmas de Computación
"""

import sys
import nltk

def check_dependencies():
    """Verifica que las dependencias estén instaladas antes de arrancar."""
    missing = []
    try:
        import nltk
    except ImportError:
        missing.append("nltk")
    try:
        import matplotlib
    except ImportError:
        missing.append("matplotlib")

    if missing:
        print("❌ Faltan dependencias. Instálalas con:")
        print(f"   pip install {' '.join(missing)}")
        sys.exit(1)

def download_nltk_data():
    """Descarga los datos de NLTK necesarios si no están presentes."""
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        print("Descargando datos de NLTK...")
        nltk.download("punkt", quiet=True)

def main():
    check_dependencies()
    download_nltk_data()

    from main_window import MainWindow
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()
