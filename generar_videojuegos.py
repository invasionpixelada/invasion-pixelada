# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE VIDEOJUEGOS
# VERSIÓN INTERNA: IP-GAMEGEN-005
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

API_KEY = os.environ.get("THEGAMESDB_API_KEY")

TIMEOUT = 20

SIMILITUD_MINIMA = 0.65
SIMILITUD_MINIMA_BASE = 0.50

MARCADOR_INICIO = (
    "<!-- VIDEOJUEGOS AUTOMÁTICOS: INICIO -->"
)

MARCADOR_FIN = (
    "<!-- VIDEOJUEGOS AUTOMÁTICOS: FIN -->"
)


# ---------------------------------------------------------
# PLATAFORMAS Y SUS IDENTIFICADORES EN THEGAMESDB
# ---------------------------------------------------------

PLATAFORMAS = [
    (
        "Sony Playstation 5",
        ["ps5", "playstation 5", "playstation5",
         "sony playstation 5"],
        "4980"
    ),
    (
        "Sony Playstation 4",
        ["ps4", "playstation 4", "playstation4",
         "sony playstation 4"],
        "4919"
    ),
    (
        "Nintendo Switch",
        ["nintendo switch", "switch"],
        "4971"
    ),
    (
        "Xbox Series X/S",
        ["xbox series x/s", "xbox series x",
         "xbox series s"],
        "4981"
    ),
    (
        "Xbox One",
        ["xbox one"],
        "4920"
    ),
    (
        "PC",
        ["pc", "windows"],
        "1"
    ),
]


# ---------------------------------------------------------
# COMPROBACIONES
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

    texto = html.unescape(str(texto or "")).lower()

    texto = texto.replace("’", "'")
    texto = texto.replace("‘", "'")
    texto = texto.replace("´", "'")

    texto = re.sub(r"[¿?¡!]", "", texto)

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

def detectar_plataforma(titulo):

    titulo_normalizado = normalizar_texto(titulo)

    for nombre, variantes, identificador in PLATAFORMAS:

        for variante in sorted(
            variantes,
            key=len,
            reverse=True
        ):

            patron = (
                r"(?<![a-z0-9])"
                + re.escape(variante)
                + r"(?![a-z0-9])"
            )

            if re.search(
                patron,
                titulo_normalizado
            ):
                return nombre, variante

    return None, None


def obtener_id_plataforma(nombre):

    if not nombre:
        return None

    buscada = normalizar_texto(nombre)

    for plataforma, variantes, identificador in PLATAFORMAS:

        if normalizar_texto(plataforma) == buscada:
            return identificador

        for variante in variantes:

            if normalizar_texto(variante) == buscada:
                return identificador

    return None


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

    return patron.sub(
        "",
        titulo
    ).strip()


# ---------------------------------------------------------
# OBTENER NOMBRE BASE
# ---------------------------------------------------------

def obtener_nombre_base(titulo):

    resultado = titulo.strip()

    # Eliminar ediciones entre paréntesis o corchetes.

    resultado = re.sub(
        r"\s*[\[(].*?(edition|edición|deluxe|collector|"
        r"collectors|limited|special|ultimate|gold|"
        r"complete|definitive|game of the year|goty|"
        r"martyrs|martyr).*?[\])]",
        "",
        resultado,
        flags=re.IGNORECASE
    )

    # Eliminar ediciones al final del título.

    resultado = re.sub(
        r"\s*[-–—:]\s*"
        r"(martyrs?[’']?\s*edition|"
        r"deluxe\s+edition|"
        r"collector'?s?\s+edition|"
        r"limited\s+edition|"
        r"special\s+edition|"
        r"ultimate\s+edition|"
        r"gold\s+edition|"
        r"complete\s+edition|"
        r"definitive\s+edition|"
        r"game\s+of\s+the\s+year|"
        r"goty|"
        r"25th\s+anniversary\s+edition)"
        r"\s*$",
        "",
        resultado,
        flags=re.IGNORECASE
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
# LEER WORD
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

            titulo_actual = texto.replace(
                "Título:",
                "",
                1
            ).strip()

        elif texto.startswith("Enlace:"):

            enlace_actual = texto.replace(
                "Enlace:",
                "",
                1
            ).strip()

        if titulo_actual and enlace_actual:

            plataforma, variante = detectar_plataforma(
                titulo_actual
            )

            titulo_juego = quitar_plataforma(
                titulo_actual,
                variante
            )

            titulo_base = obtener_nombre_base(
                titulo_juego
            )

            productos.append({
                "titulo": titulo_actual,
                "titulo_juego": titulo_juego,
                "titulo_base": titulo_base,
                "plataforma": plataforma,
                "enlace": enlace_actual
            })

            titulo_actual = None
            enlace_actual = None

    return productos


# ---------------------------------------------------------
# CONSULTAR THEGAMESDB CON FILTRO DE PLATAFORMA
# ---------------------------------------------------------

def buscar_juegos(titulo, plataforma):

    parametros = {
        "apikey": API_KEY,
        "name": titulo,
        "fields": "platform",
        "include": "platform",
        "page": 1
    }

    identificador = obtener_id_plataforma(
        plataforma
    )

    if identificador:
        parametros["filter[platform]"] = identificador

    respuesta = requests.get(
        API_URL,
        params=parametros,
        timeout=TIMEOUT
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    juegos = (
        datos.get("data", {})
        .get("games", [])
        or []
    )

    # El filtro de plataforma se aplica en la propia API.
    # No dependemos de que cada resultado incluya su nombre.

    return juegos


# ---------------------------------------------------------
# SELECCIONAR CANDIDATOS
# ---------------------------------------------------------

def obtener_palabras_significativas(texto):

    return {
        palabra
        for palabra in normalizar_texto(texto).split()
        if len(palabra) >= 4
    }


def calcular_bonus_edicion(
    titulo_producto,
    titulo_api
):

    palabras_producto = obtener_palabras_significativas(
        titulo_producto
    )

    palabras_api = obtener_palabras_significativas(
        titulo_api
    )

    if not palabras_producto:
        return 0

    coincidencias = (
        palabras_producto
        & palabras_api
    )

    return len(coincidencias) * 0.03


def seleccionar_juegos_ordenados(
    producto,
    juegos,
    busqueda_base=False
):

    candidatos = []

    if busqueda_base:

        texto_comparacion = producto["titulo_base"]
        minimo = SIMILITUD_MINIMA_BASE

    else:

        texto_comparacion = producto["titulo_juego"]
        minimo = SIMILITUD_MINIMA

    for juego in juegos:

        titulo_api = (
            juego.get("game_title")
            or juego.get("name")
            or ""
        )

        if not titulo_api:
            continue

        similitud = calcular_similitud(
            texto_comparacion,
            titulo_api
        )

        if similitud < minimo:
            continue

        puntuacion = (
            similitud
            + calcular_bonus_edicion(
                producto["titulo_juego"],
                titulo_api
            )
        )

        candidatos.append({
            "juego": juego,
            "titulo_api": titulo_api,
            "similitud": similitud,
            "puntuacion": puntuacion
        })

    candidatos.sort(
        key=lambda candidato: candidato["puntuacion"],
        reverse=True
    )

    return candidatos


# ---------------------------------------------------------
# OBTENER PORTADAS
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

    base_url = data.get(
        "base_url",
        {}
    )

    if isinstance(base_url, dict):

        base_url = (
            base_url.get("original")
            or base_url.get("large")
            or base_url.get("medium")
        )

    imagenes = data.get(
        "images",
        {}
    )

    if not base_url:
        return []

    resultados = []

    # TheGamesDB normalmente devuelve las imágenes
    # agrupadas por identificador de juego.

    if isinstance(imagenes, dict):

        listas = imagenes.values()

    elif isinstance(imagenes, list):

        listas = [imagenes]

    else:

        listas = []

    for lista in listas:

        if not isinstance(lista, list):
            continue

        for imagen in lista:

            if not isinstance(imagen, dict):
                continue

            tipo = str(
                imagen.get("type", "")
            ).lower()

            lado = str(
                imagen.get("side", "")
            ).lower()

            # Solo portadas frontales.
            if tipo and tipo != "boxart":
                continue

            if lado and lado != "front":
                continue

            filename = imagen.get("filename")

            if not filename:
                continue

            url = (
                base_url.rstrip("/")
                + "/"
                + str(filename).lstrip("/")
            )

            if url not in resultados:
                resultados.append(url)

    return resultados


# ---------------------------------------------------------
# BÚSQUEDAS ALTERNATIVAS
# ---------------------------------------------------------

def obtener_consultas(producto):

    consultas = []

    nombres = [
        producto["titulo_juego"],
        producto["titulo_base"]
    ]

    base = producto["titulo_base"]

    if ":" in base:

        nombres.append(
            base.split(":", 1)[0].strip()
        )

    if " - " in base:

        nombres.append(
            base.split(" - ", 1)[0].strip()
        )

    if " – " in base:

        nombres.append(
            base.split(" – ", 1)[0].strip()
        )

    for nombre in nombres:

        nombre = nombre.strip()

        if not nombre:
            continue

        if all(
            normalizar_texto(nombre)
            != normalizar_texto(existente)
            for existente, _ in consultas
        ):

            es_base = (
                normalizar_texto(nombre)
                != normalizar_texto(
                    producto["titulo_juego"]
                )
            )

            consultas.append(
                (nombre, es_base)
            )

    return consultas


# ---------------------------------------------------------
# BUSCAR PORTADA
# ---------------------------------------------------------

def buscar_portada(producto):

    print(
        f"  - Buscando: "
        f"{producto['titulo_juego']}"
    )

    print(
        f"  - Plataforma: "
        f"{producto['plataforma'] or 'no detectada'}"
    )

    candidatos_totales = []

    ids_vistos = set()

    consultas = obtener_consultas(
        producto
    )

    for consulta, es_base in consultas:

        print(
            f"  - Consulta: {consulta}"
        )

        try:

            juegos = buscar_juegos(
                consulta,
                producto["plataforma"]
            )

        except requests.exceptions.RequestException as error:

            print(
                f"  - Error en la consulta: {error}"
            )

            continue

        print(
            f"  - Resultados de la API: {len(juegos)}"
        )

        candidatos = seleccionar_juegos_ordenados(
            producto,
            juegos,
            busqueda_base=es_base
        )

        for candidato in candidatos:

            game_id = candidato["juego"].get("id")

            if game_id is None:
                continue

            clave = str(game_id)

            if clave in ids_vistos:
                continue

            ids_vistos.add(clave)

            candidatos_totales.append(
                candidato
            )

    candidatos_totales.sort(
        key=lambda candidato: candidato["puntuacion"],
        reverse=True
    )

    for candidato in candidatos_totales:

        juego = candidato["juego"]

        game_id = juego.get("id")

        if not game_id:
            continue

        print(
            f"  - Candidato: {candidato['titulo_api']}"
        )

        print(
            f"  - Similitud: "
            f"{candidato['similitud'] * 100:.1f}%"
        )

        print(
            f"  - Game ID: {game_id}"
        )

        try:

            imagenes = obtener_imagenes(
                game_id
            )

        except requests.exceptions.RequestException as error:

            print(
                f"  - Error consultando imágenes: {error}"
            )

            continue

        if imagenes:

            print(
                "  ✓ Portada encontrada"
            )

            return imagenes[0]

        print(
            "  - Este juego no tiene portada frontal disponible."
        )

    print(
        "  ✗ No se ha encontrado una portada válida."
    )

    return None


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

        imagen_html = f'''
                            <img
                                src="{html.escape(imagen, quote=True)}"
                                alt="{titulo}"
                                loading="lazy"
                            >
'''

    else:

        imagen_html = '''
                            <div class="store-card-placeholder-inner">
                                <span>
                                    IMAGEN NO DISPONIBLE
                                </span>
                            </div>
'''

    return f'''
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
'''


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

    if inicio == -1 or fin == -1 or fin < inicio:

        raise RuntimeError(
            "No se han encontrado los marcadores "
            "automáticos de videojuegos en tienda.html"
        )

    tarjetas = []

    for producto in productos:

        print("")

        print(
            f"Generando tarjeta: {producto['titulo']}"
        )

        try:

            imagen = buscar_portada(
                producto
            )

        except requests.exceptions.RequestException as error:

            print(
                f"  ✗ Error de TheGamesDB: {error}"
            )

            imagen = None

        except (
            ValueError,
            KeyError,
            TypeError
        ) as error:

            print(
                f"  ✗ Error procesando la respuesta: {error}"
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
    print(" VERSIÓN: IP-GAMEGEN-005")
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
        f"Videojuegos encontrados: {len(productos)}"
    )

    if not productos:

        print(
            "No hay videojuegos que generar."
        )

        return

    actualizar_tienda(productos)

    print("")
    print("----------------------------------------------")
    print("✓ tienda.html actualizada con videojuegos")
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
