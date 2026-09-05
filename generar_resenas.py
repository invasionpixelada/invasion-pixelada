from pathlib import Path
from docx import Document
import html
import re


ROOT = Path("reseñas")


def leer_docx(ruta):
    documento = Document(ruta)

    elementos = []

    for parrafo in documento.paragraphs:
        texto = parrafo.text.strip()

        if not texto:
            continue

        elementos.append(texto)

    return elementos


def escapar(texto):
    return html.escape(texto)


def crear_pagina(nombre_carpeta, contenido):
    carpeta = ROOT / nombre_carpeta

    docx = carpeta / "reseña.docx"
    portada = carpeta / "portada.jpg"

    if not docx.exists():
        return

    elementos = leer_docx(docx)

    titulo = nombre_carpeta

    if elementos:
        titulo = elementos[0]

    bloques = []

    for texto in elementos[1:]:
        if texto.startswith("[IMAGEN:"):
            numero = re.search(r"\d+", texto)

            if numero:
                n = numero.group()
                imagen = None

                for extension in ["jpg", "jpeg", "png", "webp"]:
                    posible = carpeta / f"{n}.{extension}"

                    if posible.exists():
                        imagen = posible.name
                        break

                if imagen:
                    bloques.append(
                        f'<img class="review-image" src="{imagen}" alt="">'
                    )

            continue

        if texto in [
            "Ambientación",
            "Gráficos",
            "Jugabilidad",
            "Dificultad",
            "Guion",
            "Sonido",
            "Impacto emocional",
            "Duración",
            "Finales",
            "Conclusiones",
        ]:
            bloques.append(f"<h2>{escapar(texto)}</h2>")
        else:
            bloques.append(f"<p>{escapar(texto)}</p>")

    portada_html = ""

    if portada.exists():
        portada_html = f"""
        <img
            class="review-cover"
            src="{portada.name}"
            alt="Portada de {escapar(titulo)}"
        >
        """

    contenido_html = "\n".join(bloques)

    pagina = f"""<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{escapar(titulo)} | Invasión Pixelada</title>

    <link rel="stylesheet" href="../../style.css">
</head>

<body>

<header class="site-header">

    <div class="header-content">

        <a href="../../index.html" class="logo">

            <img
                src="../../imagenes/nuevo_logo_invasion_pixelada.png"
                alt="Invasión Pixelada"
            >

            <span>Invasión Pixelada</span>

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

        <p class="section-label">
            RESEÑA
        </p>

        <h1>
            {escapar(titulo)}
        </h1>

        <div class="review-publication">
            Publicada originalmente en el CAAD
        </div>

        {portada_html}

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

    (carpeta / "index.html").write_text(
        pagina,
        encoding="utf-8"
    )


def main():
    if not ROOT.exists():
        return

    for carpeta in ROOT.iterdir():

        if carpeta.is_dir():
            crear_pagina(carpeta.name, None)


if __name__ == "__main__":
    main()
