# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE TIENDA
# VERSIÓN INTERNA: IP-STOREGEN-002
# =========================================================

from pathlib import Path
import requests
from docx import Document


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------

DOCUMENTO = Path("tienda/Libros.docx")

URL_BUSQUEDA = "https://openlibrary.org/search.json"

HEADERS = {
    "User-Agent": "InvasionPixelada/1.0 (https://invasionpixelada.github.io/invasion-pixelada/)"
}


# ---------------------------------------------------------
# LEER PRODUCTOS DEL DOCUMENTO
# ---------------------------------------------------------

def leer_productos():
    document = Document(DOCUMENTO)

    productos = []
    titulo_actual = None
    enlace_actual = None

    for paragraph in document.paragraphs:
        texto = paragraph.text.strip()

        if not texto:
            continue

        if texto.startswith("Título:"):
            titulo_actual = texto.replace("Título:", "", 1).strip()

        elif texto.startswith("Enlace:"):
            enlace_actual = texto.replace("Enlace:", "", 1).strip()

        if titulo_actual and enlace_actual:
            productos.append({
                "titulo": titulo_actual,
                "enlace": enlace_actual
            })

            titulo_actual = None
            enlace_actual = None

    return productos


# ---------------------------------------------------------
# BUSCAR PORTADA EN OPEN LIBRARY
# ---------------------------------------------------------

def buscar_portada(titulo):
    parametros = {
        "title": titulo,
        "limit": 10
    }

    respuesta = requests.get(
        URL_BUSQUEDA,
        params=parametros,
        headers=HEADERS,
        timeout=30
    )

    respuesta.raise_for_status()

    datos = respuesta.json()
    libros = datos.get("docs", [])

    if not libros:
        return None

    for libro in libros:
        cover_id = libro.get("cover_i")

        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

    return None


# ---------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------

def main():
    print("")
    print("==============================================")
    print(" INVASIÓN PIXELADA — PRUEBA OPEN LIBRARY")
    print("==============================================")
    print("")

    if not DOCUMENTO.exists():
        print(f"ERROR: No se encuentra {DOCUMENTO}")
        return

    productos = leer_productos()

    print(f"Productos encontrados en el documento: {len(productos)}")
    print("")

    encontrados = 0

    for producto in productos:
        titulo = producto["titulo"]

        print(f"Buscando: {titulo}")

        try:
            portada = buscar_portada(titulo)

            if portada:
                print("  ✓ Portada encontrada")
                print(f"  ✓ URL: {portada}")
                encontrados += 1
            else:
                print("  ✗ No se ha encontrado portada")

        except Exception as error:
            print(f"  ✗ Error: {error}")

        print("")

    print("----------------------------------------------")
    print(
        f"Resultado: {encontrados}/{len(productos)} "
        "portadas encontradas"
    )
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
