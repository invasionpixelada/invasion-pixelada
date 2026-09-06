# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE RESEÑAS
# VERSIÓN INTERNA: IP-GEN-010
# =========================================================

from pathlib import Path
from docx import Document
import html
import re
import json
from urllib.parse import quote


ROOT = Path("reseñas")
INDEX = Path("index.html")
REVIEWS_PAGE = Path("resenas.html")
SITEMAP = Path("sitemap.xml")

SITE_URL = (
    "https://invasionpixelada.github.io/invasion-pixelada"
)

SITE_NAME = "Invasión Pixelada"


# =========================================================
# UTILIDADES
# =========================================================

def escapar(texto):
    return html.escape(str(texto).strip())


def buscar_docx(carpeta):
    archivos = list(carpeta.glob("*.docx"))
    return archivos[0] if archivos else None


def buscar_imagen(carpeta, numero):
    numero = str(numero).strip()

    try:
        entero = int(numero)

        candidatos = [
            str(entero),
            f"{entero:02d}"
        ]

    except ValueError:
        candidatos = [numero]

    for nombre in candidatos:

        for extension in [
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]:

            archivo = carpeta / f"{nombre}.{extension}"

            if archivo.exists():
                return archivo.name

    return None


def buscar_portada(carpeta):

    for extension in [
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]:

        archivo = carpeta / f"portada.{extension}"

        if archivo.exists():
            return archivo.name

    return None


def crear_slug(nombre):

    texto = str(nombre).strip().lower()

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n"
    }

    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)

    texto = re.sub(
        r"[^a-z0-9]+",
        "-",
        texto
    )

    texto = texto.strip("-")

    return texto


def crear_url_reseña(nombre_carpeta):

    # Se mantiene la estructura real de carpetas
    # para no modificar las URLs actuales.

    nombre_url = quote(
        str(nombre_carpeta).strip(),
        safe=""
    )

    return (
        f"{SITE_URL}/reseñas/"
        f"{nombre_url}/"
    )


def crear_url_archivo_reseña(
    nombre_carpeta,
    nombre_archivo
):

    carpeta_url = quote(
        str(nombre_carpeta).strip(),
        safe=""
    )

    archivo_url = quote(
        str(nombre_archivo).strip(),
        safe=""
    )

    return (
        f"{SITE_URL}/reseñas/"
        f"{carpeta_url}/"
        f"{archivo_url}"
    )


# =========================================================
# LECTURA DEL DOCX
# =========================================================

def leer_docx(ruta):

    documento = Document(ruta)

    elementos = []

    for parrafo in documento.paragraphs:

        texto = parrafo.text.strip()

        if texto:
            elementos.append(texto)

    return elementos


# =========================================================
# METADATOS
# =========================================================

CAMPOS = [
    "Título",
    "Año",
    "Temática",
    "Autor",
    "Editor",
    "Plataforma",
    "Género",
    "Lanzamiento",
    "Textos",
    "Web del juego",
    "Web",
    "CAAD",
    "Enlace CAAD",
    "Valoración",
    "Puntuación",
]


def extraer_metadatos(elementos):

    metadatos = {}
    resto = []

    leyendo_metadata = True

    for texto in elementos:

        encontrado = False

        if leyendo_metadata:

            for campo in CAMPOS:

                prefijo = campo + ":"

                if texto.lower().startswith(
                    prefijo.lower()
                ):

                    valor = texto[
                        len(prefijo):
                    ].strip()

                    metadatos[
                        campo.lower()
                    ] = valor

                    encontrado = True

                    break

        if not encontrado:

            leyendo_metadata = False
            resto.append(texto)

    return metadatos, resto


def obtener(
    metadatos,
    campo,
    defecto=""
):

    return metadatos.get(
        campo.lower(),
        defecto
    )


# =========================================================
# CAAD
# =========================================================

def extraer_numero_caad(valor):

    if not valor:
        return ""

    valor = str(valor).strip()

    coincidencia = re.search(
        r"(?:n[ºo°.]?|número|numero)\s*\.?\s*(\d+)",
        valor,
        re.IGNORECASE
    )

    if coincidencia:
        return coincidencia.group(1)

    coincidencia = re.search(
        r"\b(\d+)\b",
        valor
    )

    if coincidencia:
        return coincidencia.group(1)

    return ""


# =========================================================
# ENCABEZADOS DE LA RESEÑA
# =========================================================

ENCABEZADOS = {
    "ambientación",
    "gráficos",
    "jugabilidad",
    "dificultad",
    "guion",
    "guión",
    "sonido",
    "impacto emocional",
    "duración",
    "finales",
    "conclusiones",
}


# =========================================================
# SEO
# =========================================================

def crear_meta_description(
    titulo,
    genero,
    contenido
):

    textos = []

    for texto in contenido:

        texto_limpio = texto.strip()

        if not texto_limpio:
            continue

        if texto_limpio.upper().startswith(
            "[IMAGEN:"
        ):
            continue

        if texto_limpio.lower() in ENCABEZADOS:
            continue

        textos.append(texto_limpio)

    descripcion_base = ""

    if textos:
        descripcion_base = textos[0]

    if genero:

        descripcion = (
            f"Reseña de {titulo}, "
            f"{genero.lower()}. "
            f"{descripcion_base}"
        )

    else:

        descripcion = (
            f"Reseña de {titulo} en "
            f"Invasión Pixelada. "
            f"{descripcion_base}"
        )

    descripcion = re.sub(
        r"\s+",
        " ",
        descripcion
    ).strip()

    if len(descripcion) > 155:

        descripcion = (
            descripcion[:152]
            .rsplit(" ", 1)[0]
            + "..."
        )

    return descripcion


def crear_keywords(
    titulo,
    genero,
    tematica,
    plataforma
):

    palabras = [
        titulo,
        "Invasión Pixelada",
        "reseña"
    ]

    if genero:
        palabras.append(genero)

    if tematica:
        palabras.append(tematica)

    if plataforma:
        palabras.append(plataforma)

    palabras_limpias = []

    for palabra in palabras:

        palabra = str(palabra).strip()

        if palabra and palabra not in palabras_limpias:

            palabras_limpias.append(
                palabra
            )

    return ", ".join(
        palabras_limpias
    )


def crear_json_ld(
    titulo,
    genero,
    tematica,
    año,
    autor,
    editor,
    plataforma,
    lanzamiento,
    valoracion,
    portada,
    url_reseña
):

    datos = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Review",
                "@id": f"{url_reseña}#review",
                "url": url_reseña,
                "name": f"Reseña de {titulo}",
                "headline": (
                    f"{titulo} | "
                    f"Reseña de aventura gráfica"
                ),
                "reviewBody": (
                    f"Reseña de {titulo} "
                    f"publicada por Invasión Pixelada."
                ),
                "author": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                    "url": f"{SITE_URL}/"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                    "url": f"{SITE_URL}/"
                },
                "itemReviewed": {
                    "@type": "VideoGame",
                    "name": titulo
                }
            },

            {
                "@type": "WebPage",
                "@id": f"{url_reseña}#webpage",
                "url": url_reseña,
                "name": f"{titulo} | Invasión Pixelada",
                "isPartOf": {
                    "@id": f"{SITE_URL}/#website"
                }
            },

            {
                "@type": "WebSite",
                "@id": f"{SITE_URL}/#website",
                "url": f"{SITE_URL}/",
                "name": SITE_NAME,
                "description": (
                    "Aventuras gráficas, point & click, "
                    "visual novels, walking simulators y "
                    "videojuegos donde la narrativa "
                    "es protagonista."
                ),
                "publisher": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                    "url": f"{SITE_URL}/"
                }
            },

            {
                "@type": "Organization",
                "@id": f"{SITE_URL}/#organization",
                "name": SITE_NAME,
                "url": f"{SITE_URL}/",
                "logo": {
                    "@type": "ImageObject",
                    "url": (
                        f"{SITE_URL}/"
                        "imagenes/"
                        "nuevo_logo_invasion_pixelada.png"
                    )
                },
                "sameAs": [
                    "https://www.youtube.com/@invasionpixelada"
                ]
            }
        ]
    }

    videojuego = datos["@graph"][0]["itemReviewed"]

    if genero:
        videojuego["genre"] = genero

    if tematica:
        videojuego["keywords"] = tematica

    if año:

        try:
            videojuego["datePublished"] = str(año)
        except Exception:
            pass

    if autor:

        videojuego["creator"] = {
            "@type": "Person",
            "name": autor
        }

    if editor:

        videojuego["publisher"] = {
            "@type": "Organization",
            "name": editor
        }

    if plataforma:
        videojuego["gamePlatform"] = plataforma

    if lanzamiento:
        videojuego["releaseDate"] = lanzamiento

    if valoracion:

        valoracion_limpia = str(
            valoracion
        ).replace(",", ".").strip()

        coincidencia = re.search(
            r"(\d+(?:\.\d+)?)",
            valoracion_limpia
        )

        if coincidencia:

            try:

                puntuacion = float(
                    coincidencia.group(1)
                )

                datos["@graph"][0][
                    "reviewRating"
                ] = {
                    "@type": "Rating",
                    "ratingValue": puntuacion,
                    "bestRating": 10,
                    "worstRating": 0
                }

            except ValueError:
                pass

    if portada:

        imagen_url = crear_url_archivo_reseña(
            url_reseña.split("/reseñas/")[-1].rstrip("/"),
            portada
        )

        datos["@graph"][1]["image"] = imagen_url

        videojuego["image"] = imagen_url

    return (
        '<script type="application/ld+json">\n'
        + html.escape(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=4
            ),
            quote=False
        )
        + "\n</script>"
    )


# =========================================================
# IMÁGENES DEL ARTÍCULO
# =========================================================

def obtener_imagenes(carpeta):

    imagenes = {}

    for numero in range(1, 6):

        imagen = buscar_imagen(
            carpeta,
            numero
        )

        if imagen:
            imagenes[numero] = imagen

    return imagenes


def crear_bloque_imagen(
    imagen,
    titulo
):

    return f"""
    <figure class="review-image">

        <img
            src="{escapar(imagen)}"
            alt="{escapar(titulo)}"
            loading="lazy"
        >

    </figure>
    """


# =========================================================
# CONTENIDO DE LA RESEÑA
# =========================================================

def crear_contenido(
    carpeta,
    elementos,
    titulo
):

    imagenes = obtener_imagenes(
        carpeta
    )

    bloques = []

    for texto in elementos:

        if texto.upper().startswith(
            "[IMAGEN:"
        ):
            continue

        if texto.lower() in ENCABEZADOS:

            bloques.append({
                "tipo": "heading",
                "texto": texto
            })

        else:

            bloques.append({
                "tipo": "paragraph",
                "texto": texto
            })

    if not imagenes:

        resultado = []

        for bloque in bloques:

            if bloque["tipo"] == "heading":

                resultado.append(
                    f"""
                    <h2>
                        {escapar(bloque["texto"])}
                    </h2>
                    """
                )

            else:

                resultado.append(
                    f"""
                    <p>
                        {escapar(bloque["texto"])}
                    </p>
                    """
                )

        return "\n".join(resultado)

    posiciones = {}

    for indice, bloque in enumerate(
        bloques
    ):

        if bloque["tipo"] == "heading":

            nombre = (
                bloque["texto"]
                .strip()
                .lower()
            )

            posiciones[nombre] = indice

    objetivos = {}

    # -----------------------------------------------------
    # IMAGEN 1
    # -----------------------------------------------------

    if "ambientación" in posiciones:

        objetivos[1] = max(
            0,
            posiciones["ambientación"] + 1
        )

    # -----------------------------------------------------
    # IMAGEN 2
    # -----------------------------------------------------

    if "ambientación" in posiciones:

        inicio = posiciones["ambientación"]

        siguiente = len(bloques)

        for nombre in [
            "gráficos",
            "jugabilidad"
        ]:

            if nombre in posiciones:

                siguiente = min(
                    siguiente,
                    posiciones[nombre]
                )

        objetivos[2] = min(
            inicio + 3,
            siguiente
        )

    # -----------------------------------------------------
    # IMAGEN 3
    # -----------------------------------------------------

    if "jugabilidad" in posiciones:

        inicio = posiciones["jugabilidad"]

        siguiente = len(bloques)

        for nombre in [
            "dificultad",
            "guion",
            "guión"
        ]:

            if nombre in posiciones:

                siguiente = min(
                    siguiente,
                    posiciones[nombre]
                )

        objetivos[3] = min(
            inicio + 4,
            siguiente
        )

    # -----------------------------------------------------
    # IMAGEN 4
    # -----------------------------------------------------

    if "sonido" in posiciones:

        inicio_sonido = posiciones["sonido"]

        siguiente_encabezado = len(bloques)

        for indice in range(
            inicio_sonido + 1,
            len(bloques)
        ):

            if bloques[indice]["tipo"] == "heading":

                siguiente_encabezado = indice
                break

        parrafos_sonido = []

        for indice in range(
            inicio_sonido + 1,
            siguiente_encabezado
        ):

            if bloques[indice]["tipo"] == "paragraph":

                parrafos_sonido.append(
                    indice
                )

        if len(parrafos_sonido) >= 2:

            objetivos[4] = (
                parrafos_sonido[1] + 1
            )

        elif len(parrafos_sonido) == 1:

            objetivos[4] = (
                parrafos_sonido[0] + 1
            )

        else:

            objetivos[4] = (
                inicio_sonido + 1
            )

    # -----------------------------------------------------
    # IMAGEN 5
    # -----------------------------------------------------

    inicio_final = None

    for nombre in [
        "duración",
        "finales",
        "conclusiones"
    ]:

        if nombre in posiciones:

            inicio_final = posiciones[nombre]
            break

    if inicio_final is not None:

        objetivos[5] = (
            inicio_final + 2
        )

    # -----------------------------------------------------
    # COMPLETAMOS POSICIONES
    # -----------------------------------------------------

    posiciones_ocupadas = set(
        objetivos.values()
    )

    total_bloques = len(bloques)

    for numero in sorted(imagenes):

        if numero in objetivos:
            continue

        posicion = round(
            total_bloques
            * numero
            / (len(imagenes) + 1)
        )

        posicion = max(
            0,
            min(
                posicion,
                total_bloques
            )
        )

        while posicion in posiciones_ocupadas:

            posicion += 1

            if posicion > total_bloques:
                posicion = 0

        objetivos[numero] = posicion

        posiciones_ocupadas.add(
            posicion
        )

    # -----------------------------------------------------
    # GENERAMOS EL HTML
    # -----------------------------------------------------

    resultado = []

    imagenes_pendientes = dict(
        imagenes
    )

    for indice, bloque in enumerate(
        bloques
    ):

        for numero in sorted(
            list(imagenes_pendientes.keys())
        ):

            if objetivos.get(numero) == indice:

                resultado.append(
                    crear_bloque_imagen(
                        imagenes_pendientes[numero],
                        titulo
                    )
                )

                del imagenes_pendientes[numero]

        if bloque["tipo"] == "heading":

            resultado.append(
                f"""
                <h2>
                    {escapar(bloque["texto"])}
                </h2>
                """
            )

        else:

            resultado.append(
                f"""
                <p>
                    {escapar(bloque["texto"])}
                </p>
                """
            )

    for numero in sorted(
        imagenes_pendientes
    ):

        resultado.append(
            crear_bloque_imagen(
                imagenes_pendientes[numero],
                titulo
            )
        )

    return "\n".join(resultado)


# =========================================================
# PÁGINA INDIVIDUAL
# =========================================================

def crear_pagina(
    nombre_carpeta
):

    carpeta = ROOT / nombre_carpeta

    docx = buscar_docx(carpeta)

    if not docx:
        return False

    elementos = leer_docx(docx)

    metadatos, contenido = (
        extraer_metadatos(
            elementos
        )
    )

    titulo = obtener(
        metadatos,
        "título",
        nombre_carpeta
    )

    año = obtener(
        metadatos,
        "año"
    )

    tematica = obtener(
        metadatos,
        "temática"
    )

    autor = obtener(
        metadatos,
        "autor"
    )

    editor = obtener(
        metadatos,
        "editor"
    )

    plataforma = obtener(
        metadatos,
        "plataforma"
    )

    genero = obtener(
        metadatos,
        "género"
    )

    lanzamiento = obtener(
        metadatos,
        "lanzamiento"
    )

    textos = obtener(
        metadatos,
        "textos"
    )

    web_juego = obtener(
        metadatos,
        "web del juego"
    )

    if not web_juego:

        web_juego = obtener(
            metadatos,
            "web"
        )

    caad = extraer_numero_caad(
        obtener(
            metadatos,
            "caad"
        )
    )

    enlace_caad = obtener(
        metadatos,
        "enlace caad"
    )

    valoracion = obtener(
        metadatos,
        "valoración"
    )

    if not valoracion:

        valoracion = obtener(
            metadatos,
            "puntuación"
        )

    # -----------------------------------------------------
    # SEO
    # -----------------------------------------------------

    url_reseña = crear_url_reseña(
        nombre_carpeta
    )

    meta_description = crear_meta_description(
        titulo,
        genero,
        contenido
    )

    keywords = crear_keywords(
        titulo,
        genero,
        tematica,
        plataforma
    )

    portada = buscar_portada(
        carpeta
    )

    portada_url = ""

    if portada:

        portada_url = crear_url_archivo_reseña(
            nombre_carpeta,
            portada
        )

    json_ld = crear_json_ld(
        titulo,
        genero,
        tematica,
        año,
        autor,
        editor,
        plataforma,
        lanzamiento,
        valoracion,
        portada,
        url_reseña
    )

    # -----------------------------------------------------
    # PUBLICACIÓN CAAD
    # -----------------------------------------------------

    publicacion_html = ""

    if caad:

        if enlace_caad:

            publicacion_html = f"""
            <div class="review-publication">

                Publicada originalmente en

                <a
                    href="{escapar(enlace_caad)}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    CAAD nº {escapar(caad)}
                </a>

            </div>
            """

        else:

            publicacion_html = f"""
            <div class="review-publication">

                Publicada originalmente en
                CAAD nº {escapar(caad)}

            </div>
            """

    # -----------------------------------------------------
    # PORTADA
    # -----------------------------------------------------

    portada_html = ""

    if portada:

        portada_html = f"""
        <div class="review-cover-wrap">

            <img
                class="review-cover"
                src="{escapar(portada)}"
                alt="Portada de {escapar(titulo)}"
            >

        </div>
        """

    # -----------------------------------------------------
    # FICHA
    # -----------------------------------------------------

    datos = [
        ("Año", año),
        ("Temática", tematica),
        ("Autor", autor),
        ("Editor", editor),
        ("Plataforma", plataforma),
        ("Género", genero),
        ("Lanzamiento", lanzamiento),
        ("Textos", textos),
    ]

    filas = []

    for nombre, valor in datos:

        if valor:

            filas.append(
                f"""
                <div class="review-data-row">

                    <span class="review-data-label">
                        {escapar(nombre)}
                    </span>

                    <span class="review-data-value">
                        {escapar(valor)}
                    </span>

                </div>
                """
            )

    metadata_html = ""

    if filas:

        metadata_html = f"""
        <div class="review-metadata">

            <div class="review-data-grid">

                {"".join(filas)}

            </div>

        </div>
        """

    # -----------------------------------------------------
    # VALORACIÓN
    # -----------------------------------------------------

    valoracion_html = ""

    if valoracion:

        valoracion_html = f"""
        <div class="review-rating">

            <span>
                Valoración
            </span>

            <strong>
                {escapar(valoracion)}
            </strong>

        </div>
        """

    # -----------------------------------------------------
    # WEB DEL JUEGO
    # -----------------------------------------------------

    web_html = ""

    if web_juego:

        web_html = f"""
        <div class="review-actions">

            <a
                class="review-button"
                href="{escapar(web_juego)}"
                target="_blank"
                rel="noopener noreferrer"
            >
                Visitar la web del juego
            </a>

        </div>
        """

    # -----------------------------------------------------
    # CONTENIDO
    # -----------------------------------------------------

    contenido_html = crear_contenido(
        carpeta,
        contenido,
        titulo
    )

    # -----------------------------------------------------
    # BOTONES DE NAVEGACIÓN
    # -----------------------------------------------------

    navegacion_html = """
    <div class="review-navigation">

        <a
            href="../../index.html"
            class="button secondary-button"
        >
            ← VOLVER AL INICIO
        </a>

        <a
            href="../../resenas.html"
            class="button secondary-button"
        >
            ← VOLVER A RESEÑAS
        </a>

    </div>
    """

    # -----------------------------------------------------
    # HTML DE LA PÁGINA
    # -----------------------------------------------------

    pagina = f"""<!DOCTYPE html>
<!--
    INVASIÓN PIXELADA
    PÁGINA GENERADA AUTOMÁTICAMENTE
    GENERADOR: IP-GEN-010
-->
<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {escapar(titulo)} | Reseña de aventura gráfica | Invasión Pixelada
    </title>

    <meta
        name="description"
        content="{escapar(meta_description)}"
    >

    <meta
        name="keywords"
        content="{escapar(keywords)}"
    >

    <link
        rel="canonical"
        href="{escapar(url_reseña)}"
    >

    <meta
        name="theme-color"
        content="#08080d"
    >

    <link
        rel="icon"
        type="image/png"
        href="../../imagenes/nuevo_logo_invasion_pixelada.png"
    >

    <!-- OPEN GRAPH -->

    <meta
        property="og:type"
        content="article"
    >

    <meta
        property="og:locale"
        content="es_ES"
    >

    <meta
        property="og:title"
        content="{escapar(titulo)} | Invasión Pixelada"
    >

    <meta
        property="og:description"
        content="{escapar(meta_description)}"
    >

    <meta
        property="og:url"
        content="{escapar(url_reseña)}"
    >

    <meta
        property="og:site_name"
        content="Invasión Pixelada"
    >

    <meta
        property="og:image"
        content="{escapar(portada_url if portada_url else SITE_URL + '/imagenes/nuevo_logo_invasion_pixelada.png')}"
    >

    <meta
        property="og:image:alt"
        content="Portada de {escapar(titulo)}"
    >

    {json_ld}

</head>

<body>

<header class="site-header">

    <div class="header-content">

        <a
            href="../../index.html"
            class="logo"
        >

            <img
                src="../../imagenes/nuevo_logo_invasion_pixelada.png"
                alt="Invasión Pixelada"
            >

            <span>
                Invasión Pixelada
            </span>

        </a>

        <nav class="main-nav">

            <a href="../../index.html#inicio">
                Inicio
            </a>

            <a href="../../index.html#videos">
                Vídeos
            </a>

            <a href="../../index.html#resenas">
                Reseñas
            </a>

            <a href="../../index.html#tienda">
                Tienda
            </a>

        </nav>

    </div>

</header>


<main class="review-page">

    <article class="review">

        <header class="review-header">

            <p class="section-label">
                RESEÑA
            </p>

            <h1>
                {escapar(titulo)}
            </h1>

            {publicacion_html}

        </header>

        {portada_html}

        {metadata_html}

        {valoracion_html}

        {web_html}

        <div class="review-content">

            {contenido_html}

        </div>

        {navegacion_html}

    </article>

</main>


<footer class="site-footer">

    <p>
        © 2026 Invasión Pixelada
    </p>

    <p>
        Aventuras gráficas · Narrativa · Videojuegos
    </p>

</footer>

</body>

</html>
"""

    archivo_salida = (
        carpeta / "index.html"
    )

    archivo_salida.write_text(
        pagina,
        encoding="utf-8"
    )

    return True


# =========================================================
# TARJETA DE RESEÑA
# =========================================================

def crear_tarjeta(
    nombre_carpeta,
    ruta_base="reseñas"
):

    carpeta = ROOT / nombre_carpeta

    docx = buscar_docx(carpeta)

    if not docx:
        return ""

    elementos = leer_docx(docx)

    metadatos, contenido = (
        extraer_metadatos(
            elementos
        )
    )

    titulo = obtener(
        metadatos,
        "título",
        nombre_carpeta
    )

    genero = obtener(
        metadatos,
        "género"
    )

    # -----------------------------------------------------
    # TEXTO COMPLETO PARA EL BUSCADOR
    # -----------------------------------------------------

    texto_busqueda = " ".join(
        contenido
    )

    contenido_busqueda = escapar(
        f"{titulo} {genero} {texto_busqueda}"
    )

    portada = buscar_portada(
        carpeta
    )

    descripcion = ""

    for texto in contenido:

        if texto.upper().startswith(
            "[IMAGEN:"
        ):
            continue

        if texto.strip().lower() in ENCABEZADOS:
            continue

        descripcion = texto
        break

    if len(descripcion) > 220:

        descripcion = (
            descripcion[:217]
            .rsplit(" ", 1)[0]
            + "..."
        )

    portada_html = ""

    if portada:

        portada_html = f"""
        <img
            src="{escapar(ruta_base)}/{escapar(nombre_carpeta)}/{escapar(portada)}"
            alt="Portada de {escapar(titulo)}"
            loading="lazy"
        >
        """

    genero_html = ""

    if genero:

        genero_html = f"""
        <p class="review-card-genre">
            {escapar(genero)}
        </p>
        """

    return f"""
    <article
        class="review-card"
        data-search="{contenido_busqueda}"
    >

        <a
            href="{escapar(ruta_base)}/{escapar(nombre_carpeta)}/"
            class="review-card-image"
        >

            {portada_html}

        </a>

        <div class="review-card-content">

            {genero_html}

            <h3>
                {escapar(titulo)}
            </h3>

            <p>
                {escapar(descripcion)}
            </p>

            <a
                href="{escapar(ruta_base)}/{escapar(nombre_carpeta)}/"
                class="review-card-link"
            >
                LEER RESEÑA
            </a>

        </div>

    </article>
    """


# =========================================================
# TARJETA VACÍA
# =========================================================

def crear_tarjeta_vacia():

    return """
    <article class="review-card review-card-placeholder">

        <div class="review-card-placeholder-inner">

            <span>
                PRÓXIMAMENTE
            </span>

            <h3>
                Nueva reseña
            </h3>

        </div>

    </article>
    """


# =========================================================
# OBTENER CARPETAS DE RESEÑAS
# =========================================================

def obtener_carpetas_reseñas():

    carpetas = []

    if not ROOT.exists():
        return carpetas

    for carpeta in ROOT.iterdir():

        if not carpeta.is_dir():
            continue

        docx = buscar_docx(carpeta)

        if docx:
            carpetas.append(carpeta)

    # Más reciente primero
    carpetas.sort(
        key=lambda carpeta:
            buscar_docx(carpeta).stat().st_mtime,
        reverse=True
    )

    return carpetas


# =========================================================
# ACTUALIZAR SITEMAP
# =========================================================

def actualizar_sitemap():

    urls = [
        f"{SITE_URL}/",
        f"{SITE_URL}/resenas.html",
        f"{SITE_URL}/tienda.html",
    ]

    carpetas = obtener_carpetas_reseñas()

    for carpeta in carpetas:

        urls.append(
            crear_url_reseña(
                carpeta.name
            )
        )

    contenido = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!--',
        '    INVASIÓN PIXELADA',
        '    SITEMAP GENERADO AUTOMÁTICAMENTE',
        '    GENERADOR: IP-GEN-010',
        '-->',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for url in urls:

        contenido.append(
            "    <url>"
        )

        contenido.append(
            f"        <loc>{html.escape(url)}</loc>"
        )

        contenido.append(
            "    </url>"
        )

    contenido.append(
        "</urlset>"
    )

    SITEMAP.write_text(
        "\n".join(contenido),
        encoding="utf-8"
    )

    print(
        f"Sitemap actualizado. URLs: {len(urls)}"
    )


# =========================================================
# ACTUALIZAR INDEX PRINCIPAL
# =========================================================

MARCADOR_INICIO = (
    "<!-- RESEÑAS AUTOMÁTICAS: INICIO -->"
)

MARCADOR_FIN = (
    "<!-- RESEÑAS AUTOMÁTICAS: FIN -->"
)


def actualizar_index():

    if not INDEX.exists():
        return

    html_index = INDEX.read_text(
        encoding="utf-8"
    )

    carpetas = obtener_carpetas_reseñas()

    tarjetas = []

    # Solo las tres últimas
    for carpeta in carpetas[:3]:

        tarjeta = crear_tarjeta(
            carpeta.name
        )

        if tarjeta:
            tarjetas.append(
                tarjeta
            )

    # Siempre exactamente tres espacios
    while len(tarjetas) < 3:

        tarjetas.append(
            crear_tarjeta_vacia()
        )

    contenido = f"""
{MARCADOR_INICIO}

<div class="reviews-grid">

    {"".join(tarjetas)}

</div>

{MARCADOR_FIN}
"""

    patron = re.compile(
        re.escape(MARCADOR_INICIO)
        + r".*?"
        + re.escape(MARCADOR_FIN),
        re.DOTALL
    )

    if patron.search(html_index):

        html_index = patron.sub(
            contenido.strip(),
            html_index,
            count=1
        )

    else:

        texto_vacio = (
            "Próximamente encontrarás aquí "
            "nuestras reseñas."
        )

        if texto_vacio in html_index:

            html_index = html_index.replace(
                texto_vacio,
                contenido.strip(),
                1
            )

        else:

            print(
                "No se ha encontrado la zona "
                "de reseñas en index.html."
            )

            return

    INDEX.write_text(
        html_index,
        encoding="utf-8"
    )


# =========================================================
# ACTUALIZAR PÁGINA DE TODAS LAS RESEÑAS
# =========================================================

TODAS_RESEÑAS_INICIO = (
    "<!-- TODAS LAS RESEÑAS: INICIO -->"
)

TODAS_RESEÑAS_FIN = (
    "<!-- TODAS LAS RESEÑAS: FIN -->"
)


def actualizar_resenas_html():

    if not REVIEWS_PAGE.exists():

        print(
            "resenas.html todavía no existe. "
            "Se actualizará cuando sea creada."
        )

        return

    html_resenas = REVIEWS_PAGE.read_text(
        encoding="utf-8"
    )

    carpetas = obtener_carpetas_reseñas()

    tarjetas = []

    # Todas las reseñas, de más reciente a más antigua
    for carpeta in carpetas:

        tarjeta = crear_tarjeta(
            carpeta.name,
            ruta_base="reseñas"
        )

        if tarjeta:
            tarjetas.append(
                tarjeta
            )

    contenido = f"""
{TODAS_RESEÑAS_INICIO}

<div class="reviews-grid">

    {"".join(tarjetas)}

</div>

{TODAS_RESEÑAS_FIN}
"""

    patron = re.compile(
        re.escape(TODAS_RESEÑAS_INICIO)
        + r".*?"
        + re.escape(TODAS_RESEÑAS_FIN),
        re.DOTALL
    )

    if patron.search(html_resenas):

        html_resenas = patron.sub(
            contenido.strip(),
            html_resenas,
            count=1
        )

    else:

        print(
            "No se han encontrado los marcadores "
            "de todas las reseñas en resenas.html."
        )

        return

    REVIEWS_PAGE.write_text(
        html_resenas,
        encoding="utf-8"
    )

    print(
        "Página de todas las reseñas actualizada."
    )


# =========================================================
# PROGRAMA PRINCIPAL
# =========================================================

def main():

    if not ROOT.exists():

        print(
            "No existe la carpeta reseñas."
        )

        return

    generadas = 0

    for carpeta in ROOT.iterdir():

        if not carpeta.is_dir():
            continue

        if crear_pagina(
            carpeta.name
        ):

            generadas += 1

            print(
                f"Reseña generada: "
                f"{carpeta.name}"
            )

    actualizar_index()

    actualizar_resenas_html()

    actualizar_sitemap()

    print(
        "Proceso terminado. "
        f"Reseñas generadas: {generadas}"
    )


if __name__ == "__main__":
    main()
