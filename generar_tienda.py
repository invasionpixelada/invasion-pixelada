# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE TIENDA
# VERSIÓN INTERNA: IP-STOREGEN-012
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
URL_EDICIONES = "https://openlibrary.org/works/{}/editions.json"

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
# COMPROBAR PORTADA
# ---------------------------------------------------------

def comprobar_portada(cover_id):

    if not cover_id:
        return None

    url = (
        "https://covers.openlibrary.org/"
        f"b/id/{cover_id}-L.jpg"
    )

    try:

        respuesta = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT,
            stream=True
        )

        respuesta.raise_for_status()

        content_type = respuesta.headers.get(
            "Content-Type",
            ""
        ).lower()

        if "image" not in content_type:
            return None

        return url

    except requests.exceptions.RequestException:

        return None


# ---------------------------------------------------------
# OBTENER EDICIONES DE UNA OBRA
# ---------------------------------------------------------

def obtener_ediciones(work_id):

    url = URL_EDICIONES.format(work_id)

    try:

        respuesta = requests.get(
            url,
            params={
                "limit": 100
            },
            headers=HEADERS,
            timeout=TIMEOUT
        )

        respuesta.raise_for_status()

        datos = respuesta.json()

        return datos.get("entries", [])

    except requests.exceptions.RequestException as error:

        print(
            f"  - Error obteniendo ediciones: {error}"
        )

        return []


# ---------------------------------------------------------
# BUSCAR PORTADA EN OPEN LIBRARY
# ---------------------------------------------------------

def buscar_portada(titulo):

    titulo_buscado = normalizar_titulo(titulo)

    # -----------------------------------------------------
    # IMPORTANTE:
    # Usamos q= en lugar de title=.
    #
    # La búsqueda general de Open Library encuentra obras
    # que title= puede no devolver correctamente.
    # Después nosotros comprobamos el título exacto.
    # -----------------------------------------------------

    parametros = {
        "q": titulo,
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

            obras = datos.get("docs", [])

            if not obras:

                print(
                    "  - Open Library no ha encontrado "
                    "resultados"
                )

                return None

            obras_validas = []

            for obra in obras:

                titulo_obra = obra.get(
                    "title",
                    ""
                )

                if not titulo_obra:
                    continue

                # -----------------------------------------
                # COINCIDENCIA EXACTA
                # -----------------------------------------

                if normalizar_titulo(
                    titulo_obra
                ) != titulo_buscado:

                    continue

                work_key = obra.get(
                    "key",
                    ""
                )

                if not work_key.startswith(
                    "/works/"
                ):

                    continue

                obras_validas.append({
                    "titulo": titulo_obra,
                    "key": work_key,
                    "cover_i": obra.get(
                        "cover_i"
                    )
                })

            if not obras_validas:

                print(
                    "  - No existe una obra con "
                    "título exactamente coincidente"
                )

                return None

            # -------------------------------------------------
            # RECORRER LAS OBRAS EXACTAS
            # -------------------------------------------------

            for obra in obras_validas:

                work_id = obra["key"].split(
                    "/works/"
                )[-1]

                print(
                    f"  ✓ Obra encontrada: "
                    f"{obra['titulo']}"
                )

                ediciones = obtener_ediciones(
                    work_id
                )

                candidatos = []

                # -------------------------------------------------
                # BUSCAR EDICIONES EXACTAS CON PORTADA
                # -------------------------------------------------

                for edicion in ediciones:

                    titulo_edicion = edicion.get(
                        "title",
                        ""
                    )

                    if not titulo_edicion:
                        continue

                    if normalizar_titulo(
                        titulo_edicion
                    ) != titulo_buscado:

                        continue

                    portadas = edicion.get(
                        "covers",
                        []
                    )

                    if not portadas:
                        continue

                    idiomas = edicion.get(
                        "languages",
                        []
                    )

                    if not isinstance(
                        idiomas,
                        list
                    ):
                        idiomas = []

                    idiomas_texto = []

                    for idioma in idiomas:

                        if isinstance(
                            idioma,
                            dict
                        ):

                            clave = idioma.get(
                                "key",
                                ""
                            )

                            idiomas_texto.append(
                                clave.split("/")[-1]
                            )

                    puntuacion = 100

                    # Español = prioridad,
                    # nunca requisito.
                    if "spa" in idiomas_texto:
                        puntuacion += 50

                    candidatos.append({
                        "puntuacion": puntuacion,
                        "titulo": titulo_edicion,
                        "covers": portadas,
                        "idiomas": idiomas_texto,
                        "isbn13": edicion.get(
                            "isbn_13",
                            []
                        ),
                        "isbn10": edicion.get(
                            "isbn_10",
                            []
                        )
                    })

                # -------------------------------------------------
                # ORDENAR CANDIDATOS
                # -------------------------------------------------

                candidatos.sort(
                    key=lambda x: x["puntuacion"],
                    reverse=True
                )

                # -------------------------------------------------
                # PROBAR PORTADAS DE LAS EDICIONES
                # -------------------------------------------------

                for candidato in candidatos:

                    for cover_id in candidato["covers"]:

                        portada = comprobar_portada(
                            cover_id
                        )

                        if not portada:
                            continue

                        print(
                            f"  ✓ Edición exacta: "
                            f"{candidato['titulo']}"
                        )

                        if "spa" in candidato["idiomas"]:

                            print(
                                "  ✓ Edición española "
                                "priorizada"
                            )

                        elif candidato["idiomas"]:

                            print(
                                "  - Idioma disponible: "
                                + ", ".join(
                                    candidato["idiomas"]
                                )
                            )

                        else:

                            print(
                                "  - Edición sin "
                                "información de idioma"
                            )

                        if candidato["isbn13"]:

                            print(
                                "  ✓ ISBN-13: "
                                + str(
                                    candidato["isbn13"][0]
                                )
                            )

                        elif candidato["isbn10"]:

                            print(
                                "  ✓ ISBN-10: "
                                + str(
                                    candidato["isbn10"][0]
                                )
                            )

                        print(
                            f"  ✓ Cover ID: {cover_id}"
                        )

                        return portada

                # -------------------------------------------------
                # RESPALDO: PORTADA DE LA OBRA
                #
                # Solo si no hemos encontrado una edición
                # válida. El título ya ha sido comprobado.
                # -------------------------------------------------

                cover_id = obra.get(
                    "cover_i"
                )

                if cover_id:

                    portada = comprobar_portada(
                        cover_id
                    )

                    if portada:

                        print(
                            "  ✓ Portada de la obra "
                            "encontrada"
                        )

                        print(
                            f"  ✓ Cover ID: {cover_id}"
                        )

                        return portada

            print(
                "  - No se ha encontrado "
                "ninguna portada válida"
            )

            return None

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
    print(" VERSIÓN: IP-STOREGEN-012")
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
