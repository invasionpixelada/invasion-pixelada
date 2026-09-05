# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE TIENDA
# VERSIÓN INTERNA: IP-STOREGEN-008
# =========================================================

from pathlib import Path
import re
import time
import requests
from docx import Document


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------

DOCUMENTO = Path("tienda/Libros.docx")
TIENDA_HTML = Path("tienda.html")

URL_BUSQUEDA = "https://openlibrary.org/search.json"

HEADERS = {
    "User-Agent": (
        "InvasionPixelada/1.0 "
        "(https://invasionpixelada.github.io/invasion-pixelada/)"
    )
}

MAX_INTENTOS = 3
TIMEOUT = 15

MARCADOR_INICIO = "<!-- LIBROS AUTOMÁTICOS: INICIO -->"
MARCADOR_FIN = "<!-- LIBROS AUTOMÁTICOS: FIN -->"


# ---------------------------------------------------------
# IMÁGENES LOCALES
# ---------------------------------------------------------

IMAGENES_LOCALES = {
    "Ocaso: Elige tu propia aventura": "imagenes/ocaso.jpg",
    "El terror está ahí fuera: Antología de ciencia ficción y terror Vol. 1":
        "imagenes/terror1.jpg",
    "El terror está ahí fuera: Antología de ciencia ficción y terror Vol. 2":
        "imagenes/terror2.jpg",
}


# ---------------------------------------------------------
# NORMALIZAR TÍTULOS
# ---------------------------------------------------------

def normalizar_titulo(texto):

    texto = texto.lower().strip()

    texto = texto.replace("¿", "")
    texto = texto.replace("?", "")
    texto = texto.replace("¡", "")
    texto = texto.replace("!", "")

    texto = re.sub(r"\s+", " ", texto)

    return texto


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

            titulo_actual = (
                texto.replace("Título:", "", 1).strip()
            )

        elif texto.startswith("Enlace:"):

            enlace_actual = (
                texto.replace("Enlace:", "", 1).strip()
            )

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
        "limit": 20
    }

    ultimo_error = None

    for intento in range(1, MAX_INTENTOS + 1):

        try:

            respuesta = requests.get(
                URL_BUSQUEDA,
                params=parametros,
                headers=HEADERS,
                timeout=TIMEOUT
            )

            respuesta.raise_for_status()

            datos = respuesta.json()

            libros = datos.get("docs", [])

            if not libros:
                return None

            titulo_buscado = normalizar_titulo(titulo)

            candidatos = []

            for libro in libros:

                titulo_encontrado = libro.get("title", "")

                if not titulo_encontrado:
                    continue

                titulo_normalizado = normalizar_titulo(
                    titulo_encontrado
                )

                # -----------------------------------------
                # SOLO ACEPTAMOS TÍTULOS EXACTOS
                # -----------------------------------------

                if titulo_normalizado != titulo_buscado:
                    continue

                cover_id = libro.get("cover_i")

                if not cover_id:
                    continue

                idiomas = libro.get("language", [])

                if not isinstance(idiomas, list):
                    idiomas = []

                # -----------------------------------------
                # PUNTUACIÓN
                #
                # El español se PRIORIZA cuando Open
                # Library lo indica, pero nunca se exige.
                # -----------------------------------------

                puntuacion = 100

                if "spa" in idiomas:
                    puntuacion += 50

                candidatos.append({
                    "puntuacion": puntuacion,
                    "titulo": titulo_encontrado,
                    "cover_id": cover_id,
                    "idiomas": idiomas
                })

            if not candidatos:

                print(
                    "  - No existe una coincidencia "
                    "exacta con portada"
                )

                return None

            # -----------------------------------------
            # ORDENAR
            #
            # Primero las ediciones marcadas como español.
            # Si Open Library no informa del idioma,
            # siguen siendo candidatas válidas.
            # -----------------------------------------

            candidatos.sort(
                key=lambda x: x["puntuacion"],
                reverse=True
            )

            mejor = candidatos[0]

            print(
                f"  ✓ Coincidencia exacta: "
                f"{mejor['titulo']}"
            )

            if "spa" in mejor["idiomas"]:

                print(
                    "  ✓ Edición en español priorizada"
                )

            elif mejor["idiomas"]:

                print(
                    "  - Idioma disponible, "
                    "sin español entre los datos"
                )

            else:

                print(
                    "  - Open Library no indica "
                    "el idioma de esta edición"
                )

            if mejor["idiomas"]:

                print(
                    f"  ✓ Idiomas: "
                    f"{', '.join(mejor['idiomas'])}"
                )

            return (
                "https://covers.openlibrary.org/"
                f"b/id/{mejor['cover_id']}-L.jpg"
            )

        except requests.exceptions.RequestException as error:

            ultimo_error = error

            print(
                f"  - Intento {intento}/{MAX_INTENTOS} "
                f"fallido: {error}"
            )

            if intento < MAX_INTENTOS:
                time.sleep(3)

    print(
        f"  ✗ Open Library no responde: "
        f"{ultimo_error}"
    )

    return None


# ---------------------------------------------------------
# BUSCAR IMAGEN LOCAL
# ---------------------------------------------------------

def buscar_imagen_local(titulo):

    ruta = IMAGENES_LOCALES.get(titulo)

    if not ruta:
        return None

    if Path(ruta).exists():
        return ruta

    return None


# ---------------------------------------------------------
# OBTENER IMAGEN
# ---------------------------------------------------------

def obtener_imagen(titulo):

    portada = buscar_portada(titulo)

    if portada:

        print(
            "  ✓ Portada automática aceptada"
        )

        return portada

    print(
        "  - No se ha encontrado una "
        "portada automática fiable"
    )

    imagen_local = buscar_imagen_local(titulo)

    if imagen_local:

        print(
            "  ✓ Imagen local encontrada"
        )

        return imagen_local

    print(
        "  ✗ Sin imagen"
    )

    return None


# ---------------------------------------------------------
# GENERAR TARJETA HTML
# ---------------------------------------------------------

def generar_tarjeta(producto, imagen):

    titulo = producto["titulo"]
    enlace = producto["enlace"]

    if imagen:

        imagen_html = f"""
                            <img
                                src="{imagen}"
                                alt="{titulo}"
                                loading="lazy"
                            >
"""

    else:

        imagen_html = """
                            <div class="store-card-placeholder-inner">
                                <span>
                                    IMAGEN NO DISPONIBLE
                                </span>
                            </div>
"""

    return f"""
                    <article class="store-card">

                        <a
                            href="{enlace}"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="store-card-image"
                        >

{imagen_html}

                        </a>

                        <div class="store-card-content">

                            <p class="store-card-label">
                                RECOMENDADO
                            </p>

                            <h3>
                                {titulo}
                            </h3>

                            <a
                                href="{enlace}"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="store-card-link"
                            >
                                VER EN AMAZON
                            </a>

                        </div>

                    </article>
"""


# ---------------------------------------------------------
# ACTUALIZAR TIENDA.HTML
# ---------------------------------------------------------

def actualizar_tienda(productos):

    contenido = TIENDA_HTML.read_text(
        encoding="utf-8"
    )

    inicio = contenido.find(
        MARCADOR_INICIO
    )

    fin = contenido.find(
        MARCADOR_FIN
    )

    if inicio == -1 or fin == -1:

        raise RuntimeError(
            "No se han encontrado los marcadores "
            "de libros automáticos en tienda.html"
        )

    tarjetas = []

    for producto in productos:

        print(
            f"Generando tarjeta: "
            f"{producto['titulo']}"
        )

        imagen = obtener_imagen(
            producto["titulo"]
        )

        tarjetas.append(
            generar_tarjeta(
                producto,
                imagen
            )
        )

    nuevo_bloque = (
        MARCADOR_INICIO
        + "\n"
        + "\n".join(tarjetas)
        + "\n                    "
        + MARCADOR_FIN
    )

    contenido_nuevo = (
        contenido[:inicio]
        + nuevo_bloque
        + contenido[
            fin + len(MARCADOR_FIN):
        ]
    )

    TIENDA_HTML.write_text(
        contenido_nuevo,
        encoding="utf-8"
    )


# ---------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------

def main():

    print("")
    print("==============================================")
    print(" INVASIÓN PIXELADA — GENERADOR DE TIENDA")
    print(" VERSIÓN: IP-STOREGEN-008")
    print("==============================================")
    print("")

    if not DOCUMENTO.exists():

        raise FileNotFoundError(
            f"No se encuentra {DOCUMENTO}"
        )

    if not TIENDA_HTML.exists():

        raise FileNotFoundError(
            f"No se encuentra {TIENDA_HTML}"
        )

    productos = leer_productos()

    print(
        f"Productos encontrados en el documento: "
        f"{len(productos)}"
    )

    print("")

    actualizar_tienda(productos)

    print("")
    print("----------------------------------------------")
    print("✓ tienda.html actualizada correctamente")
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
