# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE VIDEOJUEGOS
# VERSIÓN INTERNA: IP-GAMEGEN-001
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

DOCUMENTO = Path("tienda/Videojuegos.docx")
TIENDA_HTML = Path("tienda.html")

API_URL = "https://api.thegamesdb.net/v1/Games/ByGameName"
IMAGES_URL = "https://api.thegamesdb.net/v1/Games/Images"

API_KEY = os.environ.get(
    "THEGAMESDB_API_KEY"
)

TIMEOUT = 20

SIMILITUD_MINIMA = 0.80

MARCADOR_INICIO = (
    "<!-- VIDEOJUEGOS AUTOMÁTICOS: INICIO -->"
)

MARCADOR_FIN = (
    "<!-- VIDEOJUEGOS AUTOMÁTICOS: FIN -->"
)


# ---------------------------------------------------------
# COMPROBAR API KEY
# ---------------------------------------------------------

def comprobar_api_key():

    if not API_KEY:

        raise RuntimeError(
            "No se ha encontrado la variable "
            "THEGAMESDB_API_KEY."
        )


# ---------------------------------------------------------
# NORMALIZAR TEXTO
# ---------------------------------------------------------

def normalizar_texto(texto):

    texto = html.unescape(texto)

    texto = texto.lower()

    texto = texto.replace("’", "'")
    texto = texto.replace("‘", "'")

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
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ---------------------------------------------------------
# SIMILITUD
# ---------------------------------------------------------

def calcular_similitud(texto_1, texto_2):

    texto_1 = normalizar_texto(texto_1)
    texto_2 = normalizar_texto(texto_2)

    if texto_1 == texto_2:
        return 1.0

    return SequenceMatcher(
        None,
        texto_1,
        texto_2
    ).ratio()


# ---------------------------------------------------------
# DETECTAR PLATAFORMA
# ---------------------------------------------------------

PLATAFORMAS = [
    (
        "Nintendo Switch",
        [
            "nintendo switch",
            "switch"
        ]
    ),
    (
        "Sony Playstation 5",
        [
            "ps5",
            "playstation 5",
            "playstation5",
            "sony playstation 5"
        ]
    ),
    (
        "Sony Playstation 4",
        [
            "ps4",
            "playstation 4",
            "playstation4",
            "sony playstation 4"
        ]
    ),
    (
        "Xbox Series X/S",
        [
            "xbox series x",
            "xbox series s",
            "xbox series x/s"
        ]
    ),
    (
        "Xbox One",
        [
            "xbox one"
        ]
    ),
    (
        "PC",
        [
            "pc",
            "windows"
        ]
    )
]


def detectar_plataforma(titulo):

    titulo_normalizado = normalizar_texto(
        titulo
    )

    for nombre, variantes in PLATAFORMAS:

        for variante in variantes:

            if variante in titulo_normalizado:

                return nombre, variante

    return None, None


# ---------------------------------------------------------
# QUITAR PLATAFORMA DEL TÍTULO
# ---------------------------------------------------------

def quitar_plataforma(
    titulo,
    variante_plataforma
):

    if not variante_plataforma:
        return titulo.strip()

    patron = re.compile(
        r"\s*[-–—:]?\s*"
        + re.escape(variante_plataforma)
        + r"\s*$",
        re.IGNORECASE
    )

    resultado = patron.sub(
        "",
        titulo
    )

    return resultado.strip()


# ---------------------------------------------------------
# LEER PRODUCTOS
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

        if texto.upper() == "VIDEOJUEGOS":
            continue

        if texto.startswith("Título:"):

            titulo_actual = (
                texto.replace(
                    "Título:",
                    "",
                    1
                ).strip()
            )

        elif texto.startswith("Enlace:"):

            enlace_actual = (
                texto.replace(
                    "Enlace:",
                    "",
                    1
                ).strip()
            )

        if titulo_actual and enlace_actual:

            plataforma, variante = (
                detectar_plataforma(
                    titulo_actual
                )
            )

            titulo_juego = quitar_plataforma(
                titulo_actual,
                variante
            )

            productos.append({
                "titulo": titulo_actual,
                "titulo_juego": titulo_juego,
                "plataforma": plataforma,
                "enlace": enlace_actual
            })

            titulo_actual = None
            enlace_actual = None

    return productos


# ---------------------------------------------------------
# OBTENER JUEGOS DESDE THEGAMESDB
# ---------------------------------------------------------

def buscar_juegos(
    titulo,
    plataforma
):

    parametros = {
        "apikey": API_KEY,
        "name": titulo,
        "include": "platform",
        "page": 1
    }

    if plataforma:

        parametros[
            "filter[platform]"
        ] = plataforma

    respuesta = requests.get(
        API_URL,
        params=parametros,
        timeout=TIMEOUT
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    return (
        datos
        .get("data", {})
        .get("games", [])
    )


# ---------------------------------------------------------
# OBTENER IMÁGENES
# ---------------------------------------------------------

def obtener_imagenes(game_id):

    parametros = {
        "apikey": API_KEY,
        "games_id": str(game_id),
        "filter[type]": "boxart"
    }

    respuesta = requests.get(
        IMAGES_URL,
        params=parametros,
        timeout=TIMEOUT
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    data = datos.get(
        "data",
        {}
    )

    base_url = (
        data
        .get("base_url", {})
        .get("original")
    )

    imagenes = data.get(
        "images",
        []
    )

    if not base_url:
        return []

    resultados = []

    # -----------------------------------------------------
    # FORMATO HABITUAL DE THEGAMESDB
    # -----------------------------------------------------

    if isinstance(imagenes, dict):

        for lista in imagenes.values():

            if not isinstance(
                lista,
                list
            ):
                continue

            for imagen in lista:

                if not isinstance(
                    imagen,
                    dict
                ):
                    continue

                if imagen.get(
                    "side"
                ) != "front":
                    continue

                filename = imagen.get(
                    "filename"
                )

                if filename:

                    resultados.append(
                        base_url.rstrip("/")
                        + "/"
                        + filename.lstrip("/")
                    )

    elif isinstance(imagenes, list):

        for imagen in imagenes:

            if not isinstance(
                imagen,
                dict
            ):
                continue

            if imagen.get(
                "side"
            ) != "front":
                continue

            filename = imagen.get(
                "filename"
            )

            if filename:

                resultados.append(
                    base_url.rstrip("/")
                    + "/"
                    + filename.lstrip("/")
                )

    return resultados


# ---------------------------------------------------------
# BUSCAR JUEGO CORRECTO
# ---------------------------------------------------------

def seleccionar_juego(
    productos,
    juegos
):

    if not juegos:
        return None

    mejor = None
    mejor_puntuacion = 0

    for juego in juegos:

        titulo_api = juego.get(
            "game_title",
            ""
        )

        if not titulo_api:

            titulo_api = juego.get(
                "name",
                ""
            )

        if not titulo_api:
            continue

        similitud = calcular_similitud(
            productos["titulo_juego"],
            titulo_api
        )

        puntuacion = similitud

        # -------------------------------------------------
        # COINCIDENCIA DE PLATAFORMA
        # -------------------------------------------------

        if productos["plataforma"]:

            plataformas = juego.get(
                "platform",
                []
            )

            nombres_plataformas = []

            if isinstance(
                plataformas,
                list
            ):

                for plataforma in plataformas:

                    if isinstance(
                        plataforma,
                        dict
                    ):

                        nombre = plataforma.get(
                            "name",
                            ""
                        )

                        if nombre:
                            nombres_plataformas.append(
                                normalizar_texto(
                                    nombre
                                )
                            )

            elif isinstance(
                plataformas,
                dict
            ):

                nombre = plataformas.get(
                    "name",
                    ""
                )

                if nombre:
                    nombres_plataformas.append(
                        normalizar_texto(
                            nombre
                        )
                    )

            plataforma_buscada = (
                normalizar_texto(
                    productos["plataforma"]
                )
            )

            for nombre_plataforma in (
                nombres_plataformas
            ):

                if (
                    plataforma_buscada
                    in nombre_plataforma
                    or
                    nombre_plataforma
                    in plataforma_buscada
                ):

                    puntuacion += 0.30
                    break

        if puntuacion > mejor_puntuacion:

            mejor_puntuacion = puntuacion

            mejor = {
                "juego": juego,
                "titulo_api": titulo_api,
                "puntuacion": puntuacion,
                "similitud": similitud
            }

    if not mejor:
        return None

    if mejor["similitud"] < SIMILITUD_MINIMA:
        return None

    return mejor


# ---------------------------------------------------------
# BUSCAR PORTADA
# ---------------------------------------------------------

def buscar_portada(producto):

    print(
        f"  - Buscando: "
        f"{producto['titulo_juego']}"
    )

    if producto["plataforma"]:

        print(
            f"  - Plataforma: "
            f"{producto['plataforma']}"
        )

    else:

        print(
            "  - Plataforma: no detectada"
        )

    juegos = buscar_juegos(
        producto["titulo_juego"],
        producto["plataforma"]
    )

    print(
        f"  - Resultados encontrados: "
        f"{len(juegos)}"
    )

    seleccionado = seleccionar_juego(
        producto,
        juegos
    )

    if not seleccionado:

        print(
            "  ✗ No se ha encontrado "
            "un juego suficientemente similar"
        )

        return None

    juego = seleccionado["juego"]

    game_id = juego.get(
        "id"
    )

    print(
        f"  ✓ Juego encontrado: "
        f"{seleccionado['titulo_api']}"
    )

    print(
        f"  ✓ Similitud: "
        f"{seleccionado['similitud'] * 100:.1f}%"
    )

    print(
        f"  ✓ Game ID: {game_id}"
    )

    if not game_id:

        print(
            "  ✗ El resultado no tiene Game ID"
        )

        return None

    imagenes = obtener_imagenes(
        game_id
    )

    if not imagenes:

        print(
            "  ✗ No se ha encontrado "
            "boxart frontal"
        )

        return None

    print(
        "  ✓ Portada encontrada"
    )

    return imagenes[0]


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

    if inicio == -1 or fin == -1:

        raise RuntimeError(
            "No se han encontrado los "
            "marcadores automáticos "
            "de videojuegos en tienda.html"
        )

    tarjetas = []

    for producto in productos:

        print("")
        print(
            f"Generando tarjeta: "
            f"{producto['titulo']}"
        )

        try:

            imagen = buscar_portada(
                producto
            )

        except requests.exceptions.RequestException as error:

            print(
                f"  ✗ Error de TheGamesDB: "
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
    print(" GENERADOR DE VIDEOJUEGOS")
    print(" VERSIÓN: IP-GAMEGEN-001")
    print("==============================================")
    print("")

    comprobar_api_key()

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
        f"Videojuegos encontrados: "
        f"{len(productos)}"
    )

    if not productos:

        print(
            "No hay videojuegos que generar."
        )

        return

    actualizar_tienda(
        productos
    )

    print("")
    print("----------------------------------------------")
    print(
        "✓ tienda.html actualizada "
        "con videojuegos"
    )
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
