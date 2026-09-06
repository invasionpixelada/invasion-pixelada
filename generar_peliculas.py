# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE PELÍCULAS
# VERSIÓN INTERNA: IP-MOVIEGEN-001
# =========================================================

from pathlib import Path
import re
import os
import html
import requests
from difflib import SequenceMatcher
from docx import Document


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------

DOCUMENTO = Path("tienda/Peliculas.docx")
TIENDA_HTML = Path("tienda.html")

API_URL = "https://api.themoviedb.org/3/search/movie"
IMAGEN_BASE_URL = "https://image.tmdb.org/t/p/w500"

API_TOKEN = os.environ.get(
    "TMDB_API_TOKEN"
)

TIMEOUT = 20

SIMILITUD_MINIMA = 0.60
SIMILITUD_MINIMA_BASE = 0.50

MARCADOR_INICIO = (
    "<!-- PELICULAS AUTOMÁTICAS: INICIO -->"
)

MARCADOR_FIN = (
    "<!-- PELICULAS AUTOMÁTICAS: FIN -->"
)


# ---------------------------------------------------------
# COMPROBAR API TOKEN
# ---------------------------------------------------------

def comprobar_api_token():

    if not API_TOKEN:

        raise RuntimeError(
            "No se ha encontrado la variable "
            "TMDB_API_TOKEN."
        )


# ---------------------------------------------------------
# NORMALIZAR TEXTO
# ---------------------------------------------------------

def normalizar_texto(texto):

    texto = html.unescape(
        texto
    )

    texto = texto.lower()

    texto = texto.replace(
        "’",
        "'"
    )

    texto = texto.replace(
        "‘",
        "'"
    )

    texto = texto.replace(
        "´",
        "'"
    )

    texto = re.sub(
        r"[¿?¡!]",
        "",
        texto
    )

    texto = re.sub(
        r"[-–—_:,;()/]+",
        " ",
        texto
    )

    texto = re.sub(
        r"['\"]",
        "",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ---------------------------------------------------------
# SIMILITUD
# ---------------------------------------------------------

def calcular_similitud(
    texto_1,
    texto_2
):

    texto_1 = normalizar_texto(
        texto_1
    )

    texto_2 = normalizar_texto(
        texto_2
    )

    if texto_1 == texto_2:

        return 1.0

    return SequenceMatcher(
        None,
        texto_1,
        texto_2
    ).ratio()


# ---------------------------------------------------------
# DETECTAR FORMATO FÍSICO
# ---------------------------------------------------------

FORMATOS = [
    (
        "Blu-ray",
        [
            "blu-ray",
            "blu ray",
            "bluray"
        ]
    ),
    (
        "DVD",
        [
            "dvd"
        ]
    ),
    (
        "4K UHD",
        [
            "4k uhd",
            "uhd",
            "4k"
        ]
    )
]


def detectar_formato(titulo):

    titulo_normalizado = normalizar_texto(
        titulo
    )

    for nombre, variantes in FORMATOS:

        for variante in variantes:

            variante_normalizada = (
                normalizar_texto(
                    variante
                )
            )

            if variante_normalizada in (
                titulo_normalizado
            ):

                return nombre

    return None


# ---------------------------------------------------------
# QUITAR FORMATO DEL TÍTULO
# ---------------------------------------------------------

def quitar_formato(
    titulo
):

    resultado = titulo.strip()

    patron = re.compile(
        r"\s*[\[(]"
        r"\s*(blu[\s-]?ray|dvd|4k\s*uhd|uhd|4k)"
        r"\s*[\])]\s*$",
        re.IGNORECASE
    )

    resultado = patron.sub(
        "",
        resultado
    )

    resultado = re.sub(
        r"\s+",
        " ",
        resultado
    )

    return resultado.strip()


# ---------------------------------------------------------
# DETECTAR EDICIÓN / VERSIÓN
# ---------------------------------------------------------

PATRONES_EDICION = [
    (
        "final cut",
        [
            "montaje final",
            "final cut"
        ]
    ),
    (
        "director's cut",
        [
            "montaje del director",
            "montaje del director",
            "version del director",
            "versión del director",
            "director's cut",
            "directors cut"
        ]
    ),
    (
        "extended cut",
        [
            "montaje extendido",
            "version extendida",
            "versión extendida",
            "extended cut"
        ]
    ),
    (
        "theatrical cut",
        [
            "montaje cinematografico",
            "montaje cinematográfico",
            "version cinematografica",
            "versión cinematográfica",
            "theatrical cut"
        ]
    ),
    (
        "uncut",
        [
            "sin censura",
            "sin cortes",
            "uncut"
        ]
    ),
    (
        "deluxe",
        [
            "deluxe",
            "edicion deluxe",
            "edición deluxe"
        ]
    ),
    (
        "collector",
        [
            "collector",
            "collectors",
            "edicion coleccionista",
            "edición coleccionista"
        ]
    ),
    (
        "limited",
        [
            "limited",
            "edicion limitada",
            "edición limitada"
        ]
    ),
    (
        "special edition",
        [
            "special edition",
            "edicion especial",
            "edición especial"
        ]
    )
]


def detectar_edicion(
    titulo
):

    titulo_normalizado = normalizar_texto(
        titulo
    )

    ediciones_encontradas = []

    for nombre, variantes in (
        PATRONES_EDICION
    ):

        for variante in variantes:

            variante_normalizada = (
                normalizar_texto(
                    variante
                )
            )

            if variante_normalizada in (
                titulo_normalizado
            ):

                ediciones_encontradas.append(
                    nombre
                )

                break

    return ediciones_encontradas


# ---------------------------------------------------------
# OBTENER TÍTULO BASE
# ---------------------------------------------------------

def obtener_titulo_base(
    titulo
):

    resultado = titulo.strip()

    # -----------------------------------------------------
    # Eliminar información entre corchetes/paréntesis
    # que corresponda a una edición.
    # -----------------------------------------------------

    for nombre, variantes in (
        PATRONES_EDICION
    ):

        for variante in variantes:

            patron = re.compile(
                r"\s*[\[(]"
                + re.escape(variante)
                + r"[\])]",
                re.IGNORECASE
            )

            resultado = patron.sub(
                "",
                resultado
            )

    # -----------------------------------------------------
    # Eliminar expresiones de edición después de "-"
    # -----------------------------------------------------

    patrones_finales = [
        r"montaje\s+final",
        r"final\s+cut",
        r"montaje\s+del\s+director",
        r"versi[oó]n\s+del\s+director",
        r"director'?s\s+cut",
        r"montaje\s+extendido",
        r"versi[oó]n\s+extendida",
        r"extended\s+cut",
        r"deluxe\s+edition",
        r"edici[oó]n\s+deluxe",
        r"collector'?s?\s+edition",
        r"edici[oó]n\s+coleccionista",
        r"limited\s+edition",
        r"edici[oó]n\s+limitada",
        r"special\s+edition",
        r"edici[oó]n\s+especial"
    ]

    for patron_texto in patrones_finales:

        patron = re.compile(
            r"\s*[-–—:]\s*"
            + patron_texto
            + r"\s*$",
            re.IGNORECASE
        )

        resultado = patron.sub(
            "",
            resultado
        )

    resultado = re.sub(
        r"\s+",
        " ",
        resultado
    )

    resultado = re.sub(
        r"\s*[-–—:]\s*$",
        "",
        resultado
    )

    return resultado.strip()


# ---------------------------------------------------------
# LEER PRODUCTOS
# ---------------------------------------------------------

def leer_productos():

    document = Document(
        DOCUMENTO
    )

    productos = []

    titulo_actual = None
    enlace_actual = None

    for paragraph in document.paragraphs:

        texto = paragraph.text.strip()

        if not texto:

            continue

        if texto.upper() == "PELICULAS":

            continue

        if texto.startswith(
            "Título:"
        ):

            titulo_actual = (
                texto.replace(
                    "Título:",
                    "",
                    1
                ).strip()
            )

        elif texto.startswith(
            "Enlace:"
        ):

            enlace_actual = (
                texto.replace(
                    "Enlace:",
                    "",
                    1
                ).strip()
            )

        if (
            titulo_actual
            and enlace_actual
        ):

            formato = detectar_formato(
                titulo_actual
            )

            titulo_sin_formato = (
                quitar_formato(
                    titulo_actual
                )
            )

            ediciones = (
                detectar_edicion(
                    titulo_sin_formato
                )
            )

            titulo_base = (
                obtener_titulo_base(
                    titulo_sin_formato
                )
            )

            productos.append({
                "titulo": titulo_actual,
                "titulo_busqueda": titulo_sin_formato,
                "titulo_base": titulo_base,
                "ediciones": ediciones,
                "formato": formato,
                "enlace": enlace_actual
            })

            titulo_actual = None
            enlace_actual = None

    return productos


# ---------------------------------------------------------
# BUSCAR PELÍCULAS EN TMDB
# ---------------------------------------------------------

def buscar_peliculas(
    titulo
):

    parametros = {
        "query": titulo,
        "include_adult": "false",
        "language": "es-ES",
        "page": 1
    }

    cabeceras = {
        "Authorization": (
            f"Bearer {API_TOKEN}"
        ),
        "accept": "application/json"
    }

    respuesta = requests.get(
        API_URL,
        params=parametros,
        headers=cabeceras,
        timeout=TIMEOUT
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    return datos.get(
        "results",
        []
    )


# ---------------------------------------------------------
# OBTENER TÍTULO DE TMDB
# ---------------------------------------------------------

def obtener_titulo_tmdb(
    pelicula
):

    titulo = pelicula.get(
        "title",
        ""
    )

    if not titulo:

        titulo = pelicula.get(
            "original_title",
            ""
        )

    return titulo


# ---------------------------------------------------------
# OBTENER TÍTULO ORIGINAL
# ---------------------------------------------------------

def obtener_titulo_original(
    pelicula
):

    return pelicula.get(
        "original_title",
        ""
    )


# ---------------------------------------------------------
# OBTENER AÑO
# ---------------------------------------------------------

def obtener_anio(
    pelicula
):

    fecha = pelicula.get(
        "release_date",
        ""
    )

    if not fecha:

        return None

    return fecha[:4]


# ---------------------------------------------------------
# COMPROBAR EDICIÓN
# ---------------------------------------------------------

def calcular_bonus_edicion(
    producto,
    pelicula
):

    if not producto["ediciones"]:

        return 0.0

    titulo_tmdb = obtener_titulo_tmdb(
        pelicula
    )

    titulo_original = (
        obtener_titulo_original(
            pelicula
        )
    )

    texto_tmdb = (
        normalizar_texto(
            titulo_tmdb
        )
        + " "
        + normalizar_texto(
            titulo_original
        )
    )

    bonus = 0.0

    for edicion in (
        producto["ediciones"]
    ):

        if (
            normalizar_texto(
                edicion
            )
            in texto_tmdb
        ):

            bonus += 0.35

    # -----------------------------------------------------
    # Equivalencias conocidas
    # -----------------------------------------------------

    if "final cut" in (
        producto["ediciones"]
    ):

        if "final cut" in texto_tmdb:

            bonus += 0.45

    if "director's cut" in (
        producto["ediciones"]
    ):

        if (
            "director" in texto_tmdb
            and
            "cut" in texto_tmdb
        ):

            bonus += 0.45

    if "extended cut" in (
        producto["ediciones"]
    ):

        if "extended" in texto_tmdb:

            bonus += 0.45

    return bonus


# ---------------------------------------------------------
# CALCULAR PUNTUACIÓN
# ---------------------------------------------------------

def calcular_puntuacion(
    producto,
    pelicula
):

    titulo_tmdb = obtener_titulo_tmdb(
        pelicula
    )

    titulo_original = (
        obtener_titulo_original(
            pelicula
        )
    )

    # -----------------------------------------------------
    # Comparación con el título completo
    # -----------------------------------------------------

    similitud_es = calcular_similitud(
        producto["titulo_busqueda"],
        titulo_tmdb
    )

    similitud_original = 0.0

    if titulo_original:

        similitud_original = (
            calcular_similitud(
                producto["titulo_busqueda"],
                titulo_original
            )
        )

    similitud = max(
        similitud_es,
        similitud_original
    )

    puntuacion = similitud

    # -----------------------------------------------------
    # Comparación adicional con el título base
    # -----------------------------------------------------

    similitud_base = calcular_similitud(
        producto["titulo_base"],
        titulo_tmdb
    )

    similitud_base_original = 0.0

    if titulo_original:

        similitud_base_original = (
            calcular_similitud(
                producto["titulo_base"],
                titulo_original
            )
        )

    mejor_base = max(
        similitud_base,
        similitud_base_original
    )

    # -----------------------------------------------------
    # Si la búsqueda contiene una edición, el título base
    # también es importante.
    # -----------------------------------------------------

    if producto["ediciones"]:

        puntuacion += (
            mejor_base * 0.25
        )

    # -----------------------------------------------------
    # Bonus por edición
    # -----------------------------------------------------

    puntuacion += (
        calcular_bonus_edicion(
            producto,
            pelicula
        )
    )

    # -----------------------------------------------------
    # Bonus por tener cartel
    # -----------------------------------------------------

    if pelicula.get(
        "poster_path"
    ):

        puntuacion += 0.05

    return {
        "pelicula": pelicula,
        "titulo_tmdb": titulo_tmdb,
        "similitud": similitud,
        "similitud_base": mejor_base,
        "puntuacion": puntuacion
    }


# ---------------------------------------------------------
# SELECCIONAR PELÍCULA
# ---------------------------------------------------------

def seleccionar_pelicula(
    producto,
    peliculas,
    busqueda_base=False
):

    if not peliculas:

        return None

    mejor = None
    mejor_puntuacion = -1

    for pelicula in peliculas:

        titulo_tmdb = obtener_titulo_tmdb(
            pelicula
        )

        if not titulo_tmdb:

            continue

        resultado = calcular_puntuacion(
            producto,
            pelicula
        )

        if (
            resultado["puntuacion"]
            > mejor_puntuacion
        ):

            mejor_puntuacion = (
                resultado["puntuacion"]
            )

            mejor = resultado

    if not mejor:

        return None

    if busqueda_base:

        if (
            mejor["similitud_base"]
            < SIMILITUD_MINIMA_BASE
        ):

            return None

    else:

        if (
            mejor["similitud"]
            < SIMILITUD_MINIMA
            and
            mejor["similitud_base"]
            < SIMILITUD_MINIMA_BASE
        ):

            return None

    return mejor


# ---------------------------------------------------------
# BUSCAR CARTEL
# ---------------------------------------------------------

def buscar_cartel(
    producto
):

    print(
        f"  - Buscando: "
        f"{producto['titulo_busqueda']}"
    )

    print(
        f"  - Película base: "
        f"{producto['titulo_base']}"
    )

    if producto["ediciones"]:

        print(
            f"  - Edición/versión: "
            f"{', '.join(producto['ediciones'])}"
        )

    else:

        print(
            "  - Edición/versión: "
            "no especificada"
        )

    if producto["formato"]:

        print(
            f"  - Formato físico: "
            f"{producto['formato']}"
        )

    else:

        print(
            "  - Formato físico: "
            "no detectado"
        )

    # -----------------------------------------------------
    # PRIMERA BÚSQUEDA
    # -----------------------------------------------------

    peliculas = buscar_peliculas(
        producto["titulo_busqueda"]
    )

    print(
        f"  - Resultados encontrados: "
        f"{len(peliculas)}"
    )

    seleccionado = seleccionar_pelicula(
        producto,
        peliculas
    )

    # -----------------------------------------------------
    # SEGUNDA BÚSQUEDA: TÍTULO BASE
    # -----------------------------------------------------

    if not seleccionado:

        if (
            normalizar_texto(
                producto["titulo_base"]
            )
            !=
            normalizar_texto(
                producto["titulo_busqueda"]
            )
        ):

            print(
                f"  - Búsqueda alternativa: "
                f"{producto['titulo_base']}"
            )

            peliculas_base = (
                buscar_peliculas(
                    producto["titulo_base"]
                )
            )

            print(
                f"  - Resultados alternativos: "
                f"{len(peliculas_base)}"
            )

            seleccionado = (
                seleccionar_pelicula(
                    producto,
                    peliculas_base,
                    busqueda_base=True
                )
            )

    if not seleccionado:

        print(
            "  ✗ No se ha encontrado "
            "una película suficientemente similar"
        )

        return None

    pelicula = seleccionado[
        "pelicula"
    ]

    titulo_tmdb = seleccionado[
        "titulo_tmdb"
    ]

    poster_path = pelicula.get(
        "poster_path"
    )

    print(
        f"  ✓ Película encontrada: "
        f"{titulo_tmdb}"
    )

    print(
        f"  ✓ Similitud: "
        f"{seleccionado['similitud'] * 100:.1f}%"
    )

    if seleccionado[
        "similitud_base"
    ] != seleccionado[
        "similitud"
    ]:

        print(
            f"  ✓ Similitud título base: "
            f"{seleccionado['similitud_base'] * 100:.1f}%"
        )

    anio = obtener_anio(
        pelicula
    )

    if anio:

        print(
            f"  ✓ Año: {anio}"
        )

    if not poster_path:

        print(
            "  ✗ No se ha encontrado cartel"
        )

        return None

    cartel = (
        IMAGEN_BASE_URL.rstrip("/")
        + "/"
        + poster_path.lstrip("/")
    )

    print(
        "  ✓ Cartel encontrado"
    )

    return cartel


# ---------------------------------------------------------
# GENERAR TARJETA
# ---------------------------------------------------------

def generar_tarjeta(
    producto,
    imagen
):

    titulo = html.escape(
        producto["titulo"]
    )

    enlace = html.escape(
        producto["enlace"],
        quote=True
    )

    if imagen:

        imagen_html = f"""
                            <img
                                src="{html.escape(imagen, quote=True)}"
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
    productos
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

    if (
        inicio == -1
        or
        fin == -1
    ):

        raise RuntimeError(
            "No se han encontrado los "
            "marcadores automáticos "
            "de películas en tienda.html"
        )

    tarjetas = []

    for producto in productos:

        print("")
        print(
            f"Generando tarjeta: "
            f"{producto['titulo']}"
        )

        try:

            imagen = buscar_cartel(
                producto
            )

        except requests.exceptions.RequestException as error:

            print(
                f"  ✗ Error de TMDB: "
                f"{error}"
            )

            imagen = None

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
    print(" INVASIÓN PIXELADA")
    print(" GENERADOR DE PELÍCULAS")
    print(" VERSIÓN: IP-MOVIEGEN-001")
    print("==============================================")
    print("")

    comprobar_api_token()

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
        f"Películas encontradas: "
        f"{len(productos)}"
    )

    if not productos:

        print(
            "No hay películas que generar."
        )

        return

    actualizar_tienda(
        productos
    )

    print("")
    print("----------------------------------------------")
    print(
        "✓ tienda.html actualizada "
        "con películas"
    )
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":

    main()
