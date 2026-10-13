# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE VIDEOJUEGOS
# VERSIÓN INTERNA: IP-GAMEGEN-003
# =========================================================

from pathlib import Path
import re
import os
import html
import requests
from difflib import SequenceMatcher
from docx import Document

DOCUMENTO = Path("tienda/Videojuegos.docx")
TIENDA_HTML = Path("tienda.html")
API_URL = "https://api.thegamesdb.net/v1/Games/ByGameName"
IMAGES_URL = "https://api.thegamesdb.net/v1/Games/Images"
API_KEY = os.environ.get("THEGAMESDB_API_KEY")
TIMEOUT = 20
SIMILITUD_MINIMA = 0.80
SIMILITUD_MINIMA_BASE = 0.50
MARCADOR_INICIO = "<!-- VIDEOJUEGOS AUTOMÁTICOS: INICIO -->"
MARCADOR_FIN = "<!-- VIDEOJUEGOS AUTOMÁTICOS: FIN -->"

PLATAFORMAS = [
    ("Sony Playstation 5", ["ps5", "playstation 5", "playstation5", "sony playstation 5"]),
    ("Sony Playstation 4", ["ps4", "playstation 4", "playstation4", "sony playstation 4"]),
    ("Nintendo Switch", ["nintendo switch", "switch"]),
    ("Xbox Series X/S", ["xbox series x", "xbox series s", "xbox series x/s"]),
    ("Xbox One", ["xbox one"]),
    ("PC", ["pc", "windows"]),
]

ALIAS_PLATAFORMA_API = {
    "sony playstation 5": ["sony playstation 5", "playstation 5", "playstation5", "ps5"],
    "sony playstation 4": ["sony playstation 4", "playstation 4", "playstation4", "ps4"],
    "nintendo switch": ["nintendo switch", "switch"],
    "xbox series x/s": ["xbox series x", "xbox series s", "xbox series x/s", "xbox series"],
    "xbox one": ["xbox one"],
    "pc": ["pc", "windows", "computer"],
}


def comprobar_api_key():
    if not API_KEY:
        raise RuntimeError(
            "No se ha encontrado la variable THEGAMESDB_API_KEY."
        )


def normalizar_texto(texto):
    texto = html.unescape(str(texto or "")).lower()
    texto = texto.replace("’", "'").replace("‘", "'")
    texto = re.sub(r"[¿?¡!]", "", texto)
    texto = re.sub(r"[-–—_:,;()/]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


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


def detectar_plataforma(titulo):
    titulo_normalizado = normalizar_texto(titulo)

    for nombre, variantes in PLATAFORMAS:
        for variante in sorted(variantes, key=len, reverse=True):
            patron = (
                r"(?<![a-z0-9])"
                + re.escape(variante)
                + r"(?![a-z0-9])"
            )

            if re.search(patron, titulo_normalizado):
                return nombre, variante

    return None, None


def quitar_plataforma(titulo, variante_plataforma):
    if not variante_plataforma:
        return titulo.strip()

    patron = re.compile(
        r"\s*[-–—:]?\s*"
        + re.escape(variante_plataforma)
        + r"\s*$",
        re.IGNORECASE
    )

    return patron.sub("", titulo).strip()


def obtener_nombre_base(titulo):
    resultado = titulo.strip()

    resultado = re.sub(
        r"\s*[\[(].*?(edition|edición|deluxe|collector|collectors|limited|"
        r"special|ultimate|gold|complete|definitive|game of the year|goty|"
        r"martyrs|martyr).*?[\])]",
        "",
        resultado,
        flags=re.IGNORECASE
    )

    resultado = re.sub(
        r"\s*[-–—:]\s*(martyrs?[’']?\s*edition|deluxe\s+edition|"
        r"collector'?s?\s+edition|limited\s+edition|special\s+edition|"
        r"ultimate\s+edition|gold\s+edition|complete\s+edition|"
        r"definitive\s+edition|game\s+of\s+the\s+year|goty)\s*$",
        "",
        resultado,
        flags=re.IGNORECASE
    )

    resultado = re.sub(r"\s+", " ", resultado)
    resultado = re.sub(r"\s*[-–—:]\s*$", "", resultado)

    return resultado.strip()


def leer_productos():
    document = Document(DOCUMENTO)

    productos = []
    titulo_actual = None
    enlace_actual = None

    for paragraph in document.paragraphs:
        texto = paragraph.text.strip()

        if not texto or texto.upper() == "VIDEOJUEGOS":
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


def enriquecer_plataformas(juegos, mapa_plataformas):
    if not isinstance(mapa_plataformas, dict):
        mapa_plataformas = {}

    for juego in juegos:
        nombres = []
        plataforma_juego = juego.get("platform", [])

        if isinstance(plataforma_juego, dict):
            plataforma_juego = [plataforma_juego]

        if isinstance(plataforma_juego, list):
            for plataforma in plataforma_juego:
                if isinstance(plataforma, dict):
                    nombre = (
                        plataforma.get("name")
                        or plataforma.get("platform_name")
                    )

                    if nombre:
                        nombres.append(str(nombre))

                elif isinstance(plataforma, (int, str)):
                    detalle = mapa_plataformas.get(
                        str(plataforma),
                        {}
                    )

                    if isinstance(detalle, dict):
                        nombre = (
                            detalle.get("name")
                            or detalle.get("platform_name")
                        )

                        if nombre:
                            nombres.append(str(nombre))

        for clave in ("platforms", "platform_id", "platform_ids"):
            valor = juego.get(clave)

            if valor is None:
                continue

            valores = valor if isinstance(valor, list) else [valor]

            for item in valores:
                if isinstance(item, dict):
                    nombre = (
                        item.get("name")
                        or item.get("platform_name")
                    )

                    if nombre:
                        nombres.append(str(nombre))

                    identificador = item.get("id")

                else:
                    identificador = item

                if identificador is not None:
                    detalle = mapa_plataformas.get(
                        str(identificador),
                        {}
                    )

                    if isinstance(detalle, dict):
                        nombre = (
                            detalle.get("name")
                            or detalle.get("platform_name")
                        )

                        if nombre:
                            nombres.append(str(nombre))

        juego["_platform_names"] = list(dict.fromkeys(nombres))

    return juegos


def buscar_juegos(titulo, plataforma=None):
    parametros = {
        "apikey": API_KEY,
        "name": titulo,
        "include": "platform",
        "page": 1
    }

    if plataforma:
        parametros["filter[platform]"] = plataforma

    respuesta = requests.get(
        API_URL,
        params=parametros,
        timeout=TIMEOUT
    )

    respuesta.raise_for_status()
    datos = respuesta.json()

    juegos = datos.get(
        "data",
        {}
    ).get("games", []) or []

    mapa_plataformas = (
        datos.get("include", {})
        .get("platform", {})
        .get("data", {})
    )

    if not mapa_plataformas:
        mapa_plataformas = datos.get(
            "data",
            {}
        ).get("platforms", {})

    juegos = enriquecer_plataformas(
        juegos,
        mapa_plataformas
    )

    if not juegos and plataforma:
        parametros.pop("filter[platform]", None)

        respuesta = requests.get(
            API_URL,
            params=parametros,
            timeout=TIMEOUT
        )

        respuesta.raise_for_status()
        datos = respuesta.json()

        juegos = datos.get(
            "data",
            {}
        ).get("games", []) or []

        mapa_plataformas = (
            datos.get("include", {})
            .get("platform", {})
            .get("data", {})
        )

        if not mapa_plataformas:
            mapa_plataformas = datos.get(
                "data",
                {}
            ).get("platforms", {})

        juegos = enriquecer_plataformas(
            juegos,
            mapa_plataformas
        )

    return juegos


def normalizar_nombre_plataforma(nombre):
    return normalizar_texto(nombre).replace(
        "sony ",
        ""
    ).replace(
        "microsoft ",
        ""
    )


def obtener_plataformas_juego(juego):
    nombres = juego.get("_platform_names")

    if nombres is None:
        nombres = []
        plataformas = juego.get("platform", [])

        if isinstance(plataformas, dict):
            plataformas = [plataformas]

        if isinstance(plataformas, list):
            for plataforma in plataformas:
                if isinstance(plataforma, dict):
                    nombre = plataforma.get("name", "")

                    if nombre:
                        nombres.append(nombre)

    return [
        normalizar_nombre_plataforma(nombre)
        for nombre in nombres
        if nombre
    ]


def coincide_plataforma(producto, juego):
    buscada = producto.get("plataforma")

    if not buscada:
        return True

    nombres = obtener_plataformas_juego(juego)

    # Sin datos verificables de plataforma, no aceptamos
    # la coincidencia para evitar portadas de otra consola.
    if not nombres:
        return False

    alias = ALIAS_PLATAFORMA_API.get(
        normalizar_texto(buscada),
        [buscada]
    )

    alias_normalizados = [
        normalizar_nombre_plataforma(alias_item)
        for alias_item in alias
    ]

    for nombre in nombres:
        for variante in alias_normalizados:
            if (
                nombre == variante
                or variante in nombre
                or nombre in variante
            ):
                if (
                    "playstation 4" in nombre
                    and "playstation 5" in variante
                ) or (
                    "playstation 5" in nombre
                    and "playstation 4" in variante
                ):
                    continue

                return True

    return False


def obtener_palabras_significativas(texto):
    return {
        palabra
        for palabra in normalizar_texto(texto).split()
        if len(palabra) >= 4
    }


def calcular_bonus_edicion(titulo_producto, titulo_api):
    palabras_producto = obtener_palabras_significativas(
        titulo_producto
    )

    palabras_api = obtener_palabras_significativas(
        titulo_api
    )

    if not palabras_producto:
        return 0

    return len(
        palabras_producto & palabras_api
    ) * 0.05


def seleccionar_juegos_ordenados(
    producto,
    juegos,
    busqueda_base=False
):
    candidatos = []

    texto_comparacion = (
        producto["titulo_base"]
        if busqueda_base
        else producto["titulo_juego"]
    )

    minimo = (
        SIMILITUD_MINIMA_BASE
        if busqueda_base
        else SIMILITUD_MINIMA
    )

    for juego in juegos:
        titulo_api = (
            juego.get("game_title")
            or juego.get("name")
            or ""
        )

        if not titulo_api:
            continue

        if not coincide_plataforma(producto, juego):
            print(
                f"  - Descartado por plataforma: {titulo_api} "
                f"({', '.join(obtener_plataformas_juego(juego)) or 'sin datos'})"
            )
            continue

        similitud = calcular_similitud(
            texto_comparacion,
            titulo_api
        )

        if similitud < minimo:
            continue

        puntuacion = similitud + calcular_bonus_edicion(
            producto["titulo_juego"],
            titulo_api
        )

        candidatos.append({
            "juego": juego,
            "titulo_api": titulo_api,
            "puntuacion": puntuacion,
            "similitud": similitud
        })

    candidatos.sort(
        key=lambda candidato: candidato["puntuacion"],
        reverse=True
    )

    return candidatos


def seleccionar_juego(
    producto,
    juegos,
    busqueda_base=False
):
    candidatos = seleccionar_juegos_ordenados(
        producto,
        juegos,
        busqueda_base
    )

    return candidatos[0] if candidatos else None


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

    data = datos.get("data", {})
    base_url = data.get(
        "base_url",
        {}
    ).get("original")

    imagenes = data.get("images", [])

    if not base_url:
        return []

    resultados = []

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

            if str(imagen.get("side", "")).lower() != "front":
                continue

            filename = imagen.get("filename")

            if filename:
                url = (
                    base_url.rstrip("/")
                    + "/"
                    + str(filename).lstrip("/")
                )

                if url not in resultados:
                    resultados.append(url)

    return resultados


def buscar_portada(producto):
    print(f"  - Buscando: {producto['titulo_juego']}")
    print(f"  - Plataforma: {producto['plataforma'] or 'no detectada'}")

    consultas = [
        (producto["titulo_juego"], False)
    ]

    titulo_base = producto["titulo_base"]

    if (
        titulo_base
        and normalizar_texto(titulo_base)
        != normalizar_texto(producto["titulo_juego"])
    ):
        consultas.append((titulo_base, True))

    candidatos_totales = []
    vistos = set()

    for consulta, es_base in consultas:
        print(f"  - Consulta: {consulta}")

        juegos = buscar_juegos(
            consulta,
            producto["plataforma"]
        )

        print(f"  - Resultados encontrados: {len(juegos)}")

        candidatos = seleccionar_juegos_ordenados(
            producto,
            juegos,
            busqueda_base=es_base
        )

        for candidato in candidatos:
            juego_id = candidato["juego"].get("id")

            clave = (
                str(juego_id)
                if juego_id is not None
                else candidato["titulo_api"]
            )

            if clave in vistos:
                continue

            vistos.add(clave)
            candidatos_totales.append(candidato)

    candidatos_totales.sort(
        key=lambda candidato: candidato["puntuacion"],
        reverse=True
    )

    for candidato in candidatos_totales:
        juego = candidato["juego"]
        game_id = juego.get("id")

        if not game_id:
            continue

        print(f"  ✓ Candidato: {candidato['titulo_api']}")
        print(
            f"  ✓ Similitud: "
            f"{candidato['similitud'] * 100:.1f}%"
        )
        print(f"  ✓ Game ID: {game_id}")

        try:
            imagenes = obtener_imagenes(game_id)

        except requests.exceptions.RequestException as error:
            print(
                f"  - Error al consultar imágenes para "
                f"{game_id}: {error}"
            )
            continue

        if imagenes:
            print("  ✓ Portada frontal encontrada")
            return imagenes[0]

        print(
            "  - Sin portada frontal; "
            "probando el siguiente candidato."
        )

    print(
        "  ✗ No se ha encontrado una portada verificable "
        "para la plataforma solicitada."
    )

    return None


def generar_tarjeta(producto, imagen):
    titulo = html.escape(producto["titulo"])
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
                                <span>IMAGEN NO DISPONIBLE</span>
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
                            <p class="store-card-label">RECOMENDADO</p>
                            <h3>{titulo}</h3>
                            <a
                                href="{enlace}"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="store-card-link"
                            >VER EN AMAZON</a>
                        </div>
                    </article>
'''


def actualizar_tienda(productos):
    contenido = TIENDA_HTML.read_text(
        encoding="utf-8"
    )

    inicio = contenido.find(MARCADOR_INICIO)
    fin = contenido.find(MARCADOR_FIN)

    if inicio == -1 or fin == -1 or fin < inicio:
        raise RuntimeError(
            "No se han encontrado los marcadores automáticos "
            "de videojuegos en tienda.html"
        )

    tarjetas = []

    for producto in productos:
        print("")
        print(f"Generando tarjeta: {producto['titulo']}")

        try:
            imagen = buscar_portada(producto)

        except requests.exceptions.RequestException as error:
            print(f"  ✗ Error de TheGamesDB: {error}")
            imagen = None

        except (ValueError, KeyError, TypeError) as error:
            print(
                f"  ✗ Respuesta inesperada de TheGamesDB: {error}"
            )
            imagen = None

        tarjetas.append(
            generar_tarjeta(producto, imagen)
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
        + contenido[fin + len(MARCADOR_FIN):]
    )

    TIENDA_HTML.write_text(
        contenido_nuevo,
        encoding="utf-8"
    )


def main():
    print("")
    print("==============================================")
    print(" INVASIÓN PIXELADA")
    print(" GENERADOR DE VIDEOJUEGOS")
    print(" VERSIÓN: IP-GAMEGEN-003")
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
    print(f"Videojuegos encontrados: {len(productos)}")

    if not productos:
        print("No hay videojuegos que generar.")
        return

    actualizar_tienda(productos)

    print("")
    print("----------------------------------------------")
    print("✓ tienda.html actualizada con videojuegos")
    print("----------------------------------------------")
    print("")


if __name__ == "__main__":
    main()
