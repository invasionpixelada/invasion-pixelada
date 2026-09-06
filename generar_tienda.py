# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE TIENDA
# VERSIÓN INTERNA: IP-STOREGEN-016
# =========================================================

from pathlib import Path
import re
import time
import requests
from difflib import SequenceMatcher
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

SIMILITUD_MINIMA = 0.90

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

    # Eliminar signos de interrogación y exclamación.
    texto = texto.replace("¿", "")
    texto = texto.replace("?", "")
    texto = texto.replace("¡", "")
    texto = texto.replace("!", "")

    # Unificar puntuación habitual.
    texto = texto.replace(":", " ")
    texto = texto.replace("-", " ")
    texto = texto.replace("–", " ")
    texto = texto.replace("—", " ")

    # Eliminar espacios repetidos.
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


# ---------------------------------------------------------
# NORMALIZAR PARA COMPARACIÓN
# ---------------------------------------------------------

def normalizar_para_comparacion(texto):

    texto = normalizar_titulo(texto)

    palabras = texto.split()

    # Los artículos iniciales pueden variar entre la obra
    # y la edición: "Física..." / "La física..."
    while palabras and palabras[0] in {
        "el",
        "la",
        "los",
        "las",
        "un",
        "una"
    }:
        palabras.pop(0)

    return " ".join(palabras)


# ---------------------------------------------------------
# CALCULAR SIMILITUD
# ---------------------------------------------------------

def calcular_similitud(titulo_1, titulo_2):

    texto_1 = normalizar_para_comparacion(
        titulo_1
    )

    texto_2 = normalizar_para_comparacion(
        titulo_2
    )

    if texto_1 == texto_2:
        return 1.0

    return SequenceMatcher(
        None,
        texto_1,
        texto_2
    ).ratio()


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
# LEER PORTADAS EXISTENTES DE TIENDA.HTML
# ---------------------------------------------------------

def leer_portadas_existentes():

    portadas = {}

    if not TIENDA_HTML.exists():
        return portadas

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
        return portadas

    bloque = contenido[
        inicio:
        fin + len(MARCADOR_FIN)
    ]

    patrones = re.findall(
        r'<article class="store-card">.*?'
        r'<img\s+'
        r'src="([^"]+)"\s+'
        r'alt="([^"]+)"',
        bloque,
        re.DOTALL
    )

    for imagen, titulo in patrones:

        portadas[
            normalizar_titulo(titulo)
        ] = imagen

    return portadas


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
# OBTENER EDICIONES
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

    titulo_buscado = normalizar_para_comparacion(
        titulo
    )

    parametros = {
        "q": titulo,
        "limit": 20,
        "fields": (
            "key,"
            "title,"
            "author_name,"
            "cover_i,"
            "edition_key"
        )
    }

    ultimo_error = None

    for intento in range(1, MAX_INTENTOS + 1):

        try:

            # -------------------------------------------------
            # 1. BUSCAR LA OBRA
            # -------------------------------------------------

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

            # -------------------------------------------------
            # 2. LOCALIZAR OBRAS CANDIDATAS
            # -------------------------------------------------

            obras_candidatas = []

            for obra in obras:

                work_key = obra.get(
                    "key",
                    ""
                )

                if not work_key.startswith(
                    "/works/"
                ):
                    continue

                titulo_obra = obra.get(
                    "title",
                    ""
                )

                if not titulo_obra:
                    continue

                similitud = calcular_similitud(
                    titulo,
                    titulo_obra
                )

                if similitud < SIMILITUD_MINIMA:
                    continue

                puntuacion = similitud * 100

                if normalizar_para_comparacion(
                    titulo
                ) == normalizar_para_comparacion(
                    titulo_obra
                ):
                    puntuacion += 20

                obras_candidatas.append({
                    "key": work_key,
                    "titulo": titulo_obra,
                    "similitud": similitud,
                    "puntuacion": puntuacion
                })

            if not obras_candidatas:

                print(
                    "  - No se han encontrado "
                    "obras con una similitud "
                    "mínima del 90%"
                )

                return None

            obras_candidatas.sort(
                key=lambda x: x["puntuacion"],
                reverse=True
            )

            # -------------------------------------------------
            # 3. PROBAR LAS OBRAS CANDIDATAS
            # -------------------------------------------------

            for obra in obras_candidatas:

                work_id = obra["key"].split(
                    "/works/"
                )[-1]

                print(
                    f"  ✓ Obra candidata: "
                    f"{obra['titulo']}"
                )

                print(
                    f"    - Similitud: "
                    f"{obra['similitud'] * 100:.1f}%"
                )

                ediciones = obtener_ediciones(
                    work_id
                )

                if not ediciones:
                    continue

                candidatos = []

                # -------------------------------------------------
                # 4. BUSCAR EDICIONES SIMILARES
                # -------------------------------------------------

                for edicion in ediciones:

                    titulo_edicion = edicion.get(
                        "title",
                        ""
                    )

                    if not titulo_edicion:
                        continue

                    similitud_edicion = calcular_similitud(
                        titulo,
                        titulo_edicion
                    )

                    if similitud_edicion < SIMILITUD_MINIMA:
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

                    puntuacion = (
                        similitud_edicion * 100
                    )

                    if "spa" in idiomas_texto:
                        puntuacion += 50

                    candidatos.append({
                        "puntuacion": puntuacion,
                        "similitud": similitud_edicion,
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

                if not candidatos:

                    print(
                        "  - Esta obra no tiene "
                        "una edición suficientemente "
                        "similar con portada"
                    )

                    continue

                # -------------------------------------------------
                # 5. ORDENAR: ESPAÑOL + SIMILITUD
                # -------------------------------------------------

                candidatos.sort(
                    key=lambda x: x["puntuacion"],
                    reverse=True
                )

                # -------------------------------------------------
                # 6. COMPROBAR PORTADAS
                # -------------------------------------------------

                for candidato in candidatos:

                    for cover_id in candidato["covers"]:

                        portada = comprobar_portada(
                            cover_id
                        )

                        if not portada:
                            continue

                        print(
                            f"  ✓ Edición aceptada: "
                            f"{candidato['titulo']}"
                        )

                        print(
                            f"  ✓ Similitud del título: "
                            f"{candidato['similitud'] * 100:.1f}%"
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

def obtener_imagen(titulo, portadas_existentes):

    portada = buscar_portada(titulo)

    if portada:

        print(
            "  ✓ Portada automática aceptada"
        )

        return portada

    # -----------------------------------------------------
    # CONSERVAR PORTADA ANTERIOR
    # -----------------------------------------------------

    portada_anterior = portadas_existentes.get(
        normalizar_titulo(titulo)
    )

    if portada_anterior:

        print(
            "  ✓ Se conserva la portada "
            "anterior de la tienda"
        )

        return portada_anterior

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

def actualizar_tienda(
    productos,
    portadas_existentes
):

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
            producto["titulo"],
            portadas_existentes
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
    print(" VERSIÓN: IP-STOREGEN-016")
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

    # -------------------------------------------------
    # ORDEN DE PRODUCTOS
    #
    # El último producto añadido al DOCX
    # aparece primero en la tienda.
    # -------------------------------------------------

    productos.reverse()

    # -------------------------------------------------
    # PORTADAS YA EXISTENTES
    #
    # Si Open Library falla temporalmente,
    # conservamos la portada que ya tenía
    # cada producto.
    # -------------------------------------------------

    portadas_existentes = (
        leer_portadas_existentes()
    )

    actualizar_tienda(
        productos,
        portadas_existentes
    )

    print("")
    print("----------------------------------------------")
    print("✓ tienda.html actualizada correctamente")
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
