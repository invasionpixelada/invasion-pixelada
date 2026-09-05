# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE TIENDA
# VERSIÓN INTERNA: IP-STOREGEN-003
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

IMAGENES_LOCALES = {
    "Ocaso: Elige tu propia aventura": "imagenes/ocaso.jpg",
    "El terror está ahí fuera: Antología de ciencia ficción y terror Vol. 1": "imagenes/terror1.jpg",
    "El terror está ahí fuera: Antología de ciencia ficción y terror Vol. 2": "imagenes/terror2.jpg",
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
# BUSCAR IMAGEN LOCAL
# ---------------------------------------------------------

def buscar_imagen_local(titulo):
    ruta = IMAGENES_LOCALES.get(titulo)

    if not ruta:
        return None

    archivo = Path(ruta)

    if archivo.exists():
        return ruta

    return None


# ---------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------

def main():
    print("")
    print("==============================================")
    print(" INVASIÓN PIXELADA — PRUEBA DE PORTADAS")
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

        print(f"Producto: {titulo}")

        try:
            portada = buscar_portada(titulo)

            if portada:
                print("  ✓ Portada encontrada automáticamente")
                print(f"  ✓ URL: {portada}")
                encontrados += 1
                print("")
                continue

            print("  - No encontrada en Open Library")

            imagen_local = buscar_imagen_local(titulo)

            if imagen_local:
                print("  ✓ Imagen local encontrada")
                print(f"  ✓ Archivo: {imagen_local}")
                encontrados += 1
            else:
                print("  ✗ No se ha encontrado ninguna imagen")

        except Exception as error:
            print(f"  ✗ Error buscando portada: {error}")

            imagen_local = buscar_imagen_local(titulo)

            if imagen_local:
                print("  ✓ Imagen local encontrada como alternativa")
                print(f"  ✓ Archivo: {imagen_local}")
                encontrados += 1
            else:
                print("  ✗ Tampoco existe imagen local")

        print("")

    print("----------------------------------------------")
    print(
        f"Resultado: {encontrados}/{len(productos)} "
        "productos con imagen"
    )
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
