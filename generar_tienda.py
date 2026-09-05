# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE TIENDA
# VERSIÓN INTERNA: IP-STOREGEN-001
# =========================================================

from pathlib import Path
import re
import requests
from docx import Document


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------

DOCUMENTO = Path("tienda/Libros.docx")
CARPETA_PRUEBA = Path("tienda/prueba_portadas")


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
# BUSCAR LIBRO EN GOOGLE BOOKS
# ---------------------------------------------------------

def buscar_portada(titulo):
    url = "https://www.googleapis.com/books/v1/volumes"

    parametros = {
        "q": f'intitle:"{titulo}"',
        "maxResults": 5,
        "printType": "books"
    }

    respuesta = requests.get(url, params=parametros, timeout=20)
    respuesta.raise_for_status()

    datos = respuesta.json()

    libros = datos.get("items", [])

    if not libros:
        return None

    for libro in libros:
        informacion = libro.get("volumeInfo", {})
        imagenes = informacion.get("imageLinks", {})

        portada = (
            imagenes.get("extraLarge")
            or imagenes.get("large")
            or imagenes.get("medium")
            or imagenes.get("thumbnail")
        )

        if portada:
            return portada

    return None


# ---------------------------------------------------------
# DESCARGAR PORTADA
# ---------------------------------------------------------

def descargar_portada(titulo, url):
    CARPETA_PRUEBA.mkdir(parents=True, exist_ok=True)

    nombre = re.sub(r"[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+", "_", titulo)
    nombre = nombre.strip("_")

    extension = ".jpg"

    ruta = CARPETA_PRUEBA / f"{nombre}{extension}"

    respuesta = requests.get(url, timeout=20)
    respuesta.raise_for_status()

    ruta.write_bytes(respuesta.content)

    return ruta


# ---------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------

def main():
    print("")
    print("==============================================")
    print(" INVASIÓN PIXELADA — PRUEBA DE TIENDA")
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
                ruta = descargar_portada(titulo, portada)

                print(f"  ✓ Portada encontrada")
                print(f"  ✓ Guardada en: {ruta}")

                encontrados += 1

            else:
                print("  ✗ No se ha encontrado portada")

        except Exception as error:
            print(f"  ✗ Error: {error}")

        print("")

    print("----------------------------------------------")
    print(f"Resultado: {encontrados}/{len(productos)} portadas encontradas")
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
