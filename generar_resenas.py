# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE RESEÑAS
# VERSIÓN INTERNA: IP-GEN-002
# =========================================================

from pathlib import Path
from docx import Document
import html
import re


ROOT = Path("reseñas")
INDEX = Path("index.html")


# =========================================================
# UTILIDADES
# =========================================================

def escapar(texto):
    return html.escape(str(texto).strip())


def buscar_docx(carpeta):
    archivos = list(carpeta.glob("*.docx"))
    return archivos[0] if archivos else None


def buscar_imagen(carpeta, numero):
    """
    Busca imágenes con estos nombres:

    1.jpg
    01.jpg
    1.jpeg
    01.jpeg
    1.png
    01.png
    1.webp
    01.webp
    """

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
# IMÁGENES DEL ARTÍCULO
# =========================================================

def obtener_imagenes(carpeta):

    imagenes = []

    for numero in range(1, 6):

        imagen = buscar_imagen(
            carpeta,
            numero
        )

        if imagen:
            imagenes.append(imagen)

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

    # -----------------------------------------------------
    # Convertimos el documento en bloques
    # -----------------------------------------------------

    bloques = []

    for texto in elementos:

        # Los antiguos marcadores manuales se ignoran.
        # Las imágenes se colocan automáticamente.

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

    # -----------------------------------------------------
    # Si no existen imágenes, generamos solamente el texto
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Calculamos posiciones para las imágenes
    #
    # Las imágenes se introducen ENTRE bloques de texto,
    # nunca dentro de un párrafo.
    # -----------------------------------------------------

    total_bloques = len(bloques)

    posiciones = []

    if total_bloques > 0:

        for numero in range(
            len(imagenes)
        ):

            posicion = round(
                total_bloques
                * (numero + 1)
                / (len(imagenes) + 1)
            )

            posicion = max(
                1,
                min(
                    posicion,
                    total_bloques
                )
            )

            posiciones.append(
                posicion
            )

    # -----------------------------------------------------
    # Evitamos posiciones duplicadas
    # -----------------------------------------------------

    posiciones_unicas = []

    for posicion in posiciones:

        if posicion not in posiciones_unicas:

            posiciones_unicas.append(
                posicion
            )

    # Si hay más imágenes que posiciones disponibles,
    # añadimos las restantes al final.
    while len(posiciones_unicas) < len(imagenes):

        posicion = total_bloques

        if posicion not in posiciones_unicas:

            posiciones_unicas.append(
                posicion
            )

        else:

            posicion += 1

            posiciones_unicas.append(
                posicion
            )

    posiciones_unicas = sorted(
        posiciones_unicas
    )

    # -----------------------------------------------------
    # Generamos el HTML
    # -----------------------------------------------------

    resultado = []

    indice_imagen = 0

    for indice, bloque in enumerate(
        bloques,
        start=1
    ):

        # Insertamos la imagen ANTES del bloque
        # correspondiente.
        if (
            indice_imagen < len(imagenes)
            and indice in posiciones_unicas
        ):

            resultado.append(
                crear_bloque_imagen(
                    imagenes[indice_imagen],
                    titulo
                )
            )

            indice_imagen += 1

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

    # -----------------------------------------------------
    # Si queda alguna imagen, la colocamos al final.
    # -----------------------------------------------------

    while indice_imagen < len(imagenes):

        resultado.append(
            crear_bloque_imagen(
                imagenes[indice_imagen],
                titulo
            )
        )

        indice_imagen += 1

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

    portada = buscar_portada(
        carpeta
    )

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
    # HTML DE LA PÁGINA
    # -----------------------------------------------------

    pagina = f"""<!DOCTYPE html>
<!--
    INVASIÓN PIXELADA
    PÁGINA GENERADA AUTOMÁTICAMENTE
    GENERADOR: IP-GEN-002
-->
<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {escapar(titulo)} | Invasión Pixelada
    </title>

    <link
        rel="stylesheet"
        href="../../style.css"
    >

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
    nombre_carpeta
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
            src="reseñas/{escapar(nombre_carpeta)}/{escapar(portada)}"
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
    <article class="review-card">

        <a
            href="reseñas/{escapar(nombre_carpeta)}/"
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
                href="reseñas/{escapar(nombre_carpeta)}/"
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

    carpetas = []

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

    print(
        "Proceso terminado. "
        f"Reseñas generadas: {generadas}"
    )


if __name__ == "__main__":
    main()
