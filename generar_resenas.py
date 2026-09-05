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
    numero = str(numero).strip()

    try:
        entero = int(numero)
        candidatos = [str(entero), f"{entero:02d}"]
    except ValueError:
        candidatos = [numero]

    for nombre in candidatos:
        for extension in ["jpg", "jpeg", "png", "webp"]:
            archivo = carpeta / f"{nombre}.{extension}"

            if archivo.exists():
                return archivo.name

    return None


def buscar_portada(carpeta):
    for extension in ["jpg", "jpeg", "png", "webp"]:
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

                if texto.lower().startswith(prefijo.lower()):

                    valor = texto[len(prefijo):].strip()

                    metadatos[campo.lower()] = valor

                    encontrado = True
                    break

        if not encontrado:
            leyendo_metadata = False
            resto.append(texto)

    return metadatos, resto


def obtener(metadatos, campo, defecto=""):
    return metadatos.get(campo.lower(), defecto)


# =========================================================
# CAAD
# =========================================================

def extraer_numero_caad(valor):

    if not valor:
        return ""

    coincidencia = re.search(
        r"(?:n[ºo°.]?|número|numero)\s*(\d+)",
        valor,
        re.IGNORECASE
    )

    if coincidencia:
        return coincidencia.group(1)

    coincidencia = re.search(r"\b(\d+)\b", valor)

    if coincidencia:
        return coincidencia.group(1)

    return valor.strip()


# =========================================================
# ENCABEZADOS
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
# CONTENIDO
# =========================================================

def crear_contenido(carpeta, elementos):

    bloques = []

    for texto in elementos:

        # IMAGEN

        if texto.upper().startswith("[IMAGEN:"):

            numero = re.search(r"\d+", texto)

            if numero:

                imagen = buscar_imagen(
                    carpeta,
                    numero.group()
                )

                if imagen:

                    bloques.append(
                        f"""
                        <figure class="review-image">
                            <img
                                src="{escapar(imagen)}"
                                alt=""
                                loading="lazy"
                            >
                        </figure>
                        """
                    )

            continue

        # ENCABEZADO

        if texto.strip().lower() in ENCABEZADOS:

            bloques.append(
                f"""
                <h2>{escapar(texto)}</h2>
                """
            )

            continue

        # PÁRRAFO

        bloques.append(
            f"""
            <p>{escapar(texto)}</p>
            """
        )

    return "\n".join(bloques)


# =========================================================
# PÁGINA INDIVIDUAL
# =========================================================

def crear_pagina(nombre_carpeta):

    carpeta = ROOT / nombre_carpeta

    docx = buscar_docx(carpeta)

    if not docx:
        return False

    elementos = leer_docx(docx)

    metadatos, contenido = extraer_metadatos(elementos)

    titulo = obtener(metadatos, "título", nombre_carpeta)
    año = obtener(metadatos, "año")
    tematica = obtener(metadatos, "temática")
    autor = obtener(metadatos, "autor")
    editor = obtener(metadatos, "editor")
    plataforma = obtener(metadatos, "plataforma")
    genero = obtener(metadatos, "género")
    lanzamiento = obtener(metadatos, "lanzamiento")
    textos = obtener(metadatos, "textos")

    web_juego = obtener(metadatos, "web del juego")

    if not web_juego:
        web_juego = obtener(metadatos, "web")

    caad = extraer_numero_caad(
        obtener(metadatos, "caad")
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
                Publicada originalmente en CAAD nº {escapar(caad)}
            </div>
            """

    # -----------------------------------------------------
    # PORTADA
    # -----------------------------------------------------

    portada = buscar_portada(carpeta)

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
            <span>Valoración</span>
            <strong>{escapar(valoracion)}</strong>
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
        contenido
    )

    # -----------------------------------------------------
    # HTML FINAL
    # -----------------------------------------------------

    pagina = f"""<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>{escapar(titulo)} | Invasión Pixelada</title>

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

            <span>Invasión Pixelada</span>

        </a>

        <nav class="main-nav">

            <a href="../../index.html#inicio">Inicio</a>
            <a href="../../index.html#videos">Vídeos</a>
            <a href="../../index.html#resenas">Reseñas</a>
            <a href="../../index.html#tienda">Tienda</a>

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

    <p>© 2026 Invasión Pixelada</p>

    <p>
        Aventuras gráficas · Narrativa · Videojuegos
    </p>

</footer>

</body>

</html>
"""

    archivo_salida = carpeta / "index.html"

    archivo_salida.write_text(
        pagina,
        encoding="utf-8"
    )

    return True


# =========================================================
# TARJETA DE RESEÑA
# =========================================================

def crear_tarjeta(nombre_carpeta):

    carpeta = ROOT / nombre_carpeta

    docx = buscar_docx(carpeta)

    if not docx:
        return ""

    elementos = leer_docx(docx)

    metadatos, contenido = extraer_metadatos(elementos)

    titulo = obtener(
        metadatos,
        "título",
        nombre_carpeta
    )

    genero = obtener(
        metadatos,
        "género"
    )

    portada = buscar_portada(carpeta)

    descripcion = ""

    for texto in contenido:

        if texto.upper().startswith("[IMAGEN:"):
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

            <span>PRÓXIMAMENTE</span>

            <h3>
                Nueva reseña
            </h3>

        </div>

    </article>
    """


# =========================================================
# ACTUALIZAR INDEX
# =========================================================

MARCADOR_INICIO = "<!-- RESEÑAS AUTOMÁTICAS: INICIO -->"
MARCADOR_FIN = "<!-- RESEÑAS AUTOMÁTICAS: FIN -->"


def actualizar_index():

    if not INDEX.exists():
        return

    html_index = INDEX.read_text(
        encoding="utf-8"
    )

    tarjetas = []

    carpetas = []

    for carpeta in ROOT.iterdir():

        if not carpeta.is_dir():
            continue

        if buscar_docx(carpeta):
            carpetas.append(carpeta)

    # Las carpetas se ordenan por fecha de modificación.
    # La más reciente aparece primero.
    carpetas.sort(
        key=lambda carpeta: buscar_docx(carpeta).stat().st_mtime,
        reverse=True
    )

    # Solo las 3 más recientes aparecen en portada.
    ultimas = carpetas[:3]

    for carpeta in ultimas:

        tarjeta = crear_tarjeta(
            carpeta.name
        )

        if tarjeta:
            tarjetas.append(tarjeta)

    # Rellenamos hasta tener exactamente 3 espacios.
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
            "Próximamente encontrarás aquí nuestras reseñas."
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

        if crear_pagina(carpeta.name):

            generadas += 1

            print(
                f"Reseña generada: {carpeta.name}"
            )

    actualizar_index()

    print(
        "Proceso terminado. "
        f"Reseñas generadas: {generadas}"
    )


if __name__ == "__main__":
    main()
