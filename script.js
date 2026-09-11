/*
    INVASIÓN PIXELADA
    VERSIÓN INTERNA: IP-JS-003
*/


/* =========================================================
   VÍDEOS DE YOUTUBE
   ========================================================= */

const API_KEY = "AIzaSyAE_wqprOnVFSdGDb2-qMWqtkutgwfoHXQ";
const CHANNEL_HANDLE = "@invasionpixelada";


async function cargarVideos() {

    const tarjetas = document.querySelectorAll(".video-card");

    try {

        // 1. Obtener información del canal
        const channelResponse = await fetch(
            `https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle=${encodeURIComponent(CHANNEL_HANDLE)}&key=${API_KEY}`
        );

        const channelData = await channelResponse.json();

        if (!channelData.items || channelData.items.length === 0) {
            throw new Error("No se ha encontrado el canal.");
        }

        const uploadsPlaylistId =
            channelData.items[0].contentDetails.relatedPlaylists.uploads;


        // 2. Obtener los 6 vídeos más recientes
        const videosResponse = await fetch(
            `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=${uploadsPlaylistId}&maxResults=6&key=${API_KEY}`
        );

        const videosData = await videosResponse.json();

        if (!videosData.items) {
            throw new Error("No se han encontrado vídeos.");
        }


        // 3. Rellenar las tarjetas
        videosData.items.forEach((video, index) => {

            if (!tarjetas[index]) return;

            const snippet = video.snippet;
            const videoId = snippet.resourceId.videoId;

            const enlace =
                tarjetas[index].querySelector(".video-link");

            const imagen =
                tarjetas[index].querySelector(".video-placeholder");

            const titulo =
                tarjetas[index].querySelector("h3");

            const informacion =
                tarjetas[index].querySelector("p");


            // Enlace al vídeo
            enlace.href =
                `https://www.youtube.com/watch?v=${videoId}`;


            // Miniatura
            imagen.innerHTML = `
                <img
                    src="${snippet.thumbnails.high.url}"
                    alt="${snippet.title}"
                    loading="lazy"
                >
            `;


            // Título
            titulo.textContent = snippet.title;


            // Fecha
            const fecha =
                new Date(snippet.publishedAt);

            informacion.textContent =
                fecha.toLocaleDateString("es-ES", {
                    day: "numeric",
                    month: "long",
                    year: "numeric"
                });

        });

    } catch (error) {

        console.error(
            "Error al cargar los vídeos:",
            error
        );

    }
}


/* =========================================================
   NOTICIAS
   ========================================================= */

const NUMERO_NOTICIAS =
    6;


/*
    Palabras y conceptos relacionados con el contenido
    de Invasión Pixelada.

    Se utilizarán para seleccionar las noticias del RSS
    que tengan relación con:

    - Aventuras gráficas
    - Point & Click
    - Videojuegos narrativos
    - Visual novels
    - Walking simulators
    - Misterio
    - Terror narrativo
    - Ciencia ficción narrativa
    - Juegos centrados en la historia
*/

const PALABRAS_NOTICIAS = [

    "aventura gráfica",
    "aventura grafica",
    "point & click",
    "point and click",
    "point-and-click",
    "visual novel",
    "visual novels",
    "novela visual",
    "walking simulator",
    "walking simulators",
    "narrativo",
    "narrativa",
    "narración",
    "historia",
    "misterio",
    "terror",
    "horror",
    "lovecraft",
    "lovecraftiano",
    "ciencia ficción",
    "ciencia ficcion",
    "thriller",
    "detective",
    "investigación",
    "investigacion",
    "puzles",
    "puzzles"
];


/*
    Comprueba si una noticia tiene relación con
    el contenido de Invasión Pixelada.
*/

function noticiaEsRelevante(noticia) {

    const texto = `
        ${noticia.title || ""}
        ${noticia.description || ""}
        ${noticia.category || ""}
    `.toLowerCase();


    return PALABRAS_NOTICIAS.some(
        palabra => texto.includes(palabra)
    );

}


/*
    Formatea la fecha de la noticia.
*/

function formatearFechaNoticia(fechaOriginal) {

    const fecha =
        new Date(fechaOriginal);


    if (Number.isNaN(fecha.getTime())) {
        return "";
    }


    return fecha.toLocaleDateString(
        "es-ES",
        {
            day: "numeric",
            month: "long",
            year: "numeric"
        }
    );

}


/*
    Carga las noticias desde noticias.json.

    Este archivo será generado automáticamente
    a partir del RSS de uVeJuegos mediante
    GitHub Actions.
*/

async function cargarNoticias() {

    const contenedor =
        document.querySelector("#news-grid");


    if (!contenedor) {
        return;
    }


    try {

        const respuesta =
            await fetch(
                "noticias.json?nocache=" +
                Date.now()
            );


        if (!respuesta.ok) {

            throw new Error(
                "No se ha podido cargar noticias.json."
            );

        }


        const datos =
            await respuesta.json();


        if (!Array.isArray(datos)) {

            throw new Error(
                "El archivo de noticias no tiene un formato válido."
            );

        }


        /*
            Filtramos las noticias relacionadas
            con la temática de la web.
        */

        const noticiasRelevantes =
            datos
                .filter(noticiaEsRelevante)
                .slice(0, NUMERO_NOTICIAS);


        /*
            Si no encontramos noticias relevantes,
            mostramos un mensaje.
        */

        if (
            noticiasRelevantes.length === 0
        ) {

            contenedor.innerHTML = `
                <p class="news-empty">
                    No hay noticias relacionadas
                    con nuestra temática en este momento.
                </p>
            `;

            return;
        }


        /*
            Limpiamos el contenido inicial.
        */

        contenedor.innerHTML = "";


        /*
            Creamos las tarjetas.
        */

        noticiasRelevantes.forEach(
            noticia => {

                const articulo =
                    document.createElement("article");

                articulo.className =
                    "news-card";


                /*
                    Fecha
                */

                const fecha =
                    formatearFechaNoticia(
                        noticia.pubDate
                    );


                /*
                    Etiqueta de fuente
                */

                const fuente =
                    document.createElement("p");

                fuente.className =
                    "news-card-source";

                fuente.textContent =
                    "uVeJuegos";


                /*
                    Título
                */

                const titulo =
                    document.createElement("h3");

                titulo.textContent =
                    noticia.title || "Noticia";


                /*
                    Descripción
                */

                const descripcion =
                    document.createElement("p");

                descripcion.className =
                    "news-card-description";

                descripcion.textContent =
                    noticia.description || "";


                /*
                    Fecha
                */

                const fechaElemento =
                    document.createElement("p");

                fechaElemento.className =
                    "news-card-date";

                fechaElemento.textContent =
                    fecha;


                /*
                    Enlace a la noticia original
                */

                const enlace =
                    document.createElement("a");

                enlace.className =
                    "news-card-link";

                enlace.href =
                    noticia.link;

                enlace.target =
                    "_blank";

                enlace.rel =
                    "noopener noreferrer";

                enlace.textContent =
                    "LEER NOTICIA";


                /*
                    Construimos la tarjeta.
                */

                articulo.appendChild(
                    fuente
                );

                articulo.appendChild(
                    titulo
                );

                articulo.appendChild(
                    descripcion
                );

                if (fecha) {

                    articulo.appendChild(
                        fechaElemento
                    );

                }

                articulo.appendChild(
                    enlace
                );


                contenedor.appendChild(
                    articulo
                );

            }
        );


    } catch (error) {

        console.error(
            "Error al cargar las noticias:",
            error
        );


        contenedor.innerHTML = `
            <p class="news-empty">
                No se han podido cargar las noticias en este momento.
            </p>
        `;

    }

}


/* =========================================================
   PAGINACIÓN DE LA TIENDA
   ========================================================= */

const PRODUCTOS_POR_PAGINA = 9;


function crearPaginacionTienda() {

    const categorias =
        document.querySelectorAll(".store-category");


    categorias.forEach((categoria) => {

        const grid =
            categoria.querySelector(".store-grid");

        const paginacion =
            categoria.querySelector(".store-pagination");


        if (!grid || !paginacion) return;


        const productos =
            Array.from(grid.children).filter((elemento) =>
                elemento.matches(".store-card")
            );


        // Si no hay más de 9 productos,
        // no necesitamos paginación.
        if (productos.length <= PRODUCTOS_POR_PAGINA) {

            paginacion.innerHTML = "";
            paginacion.style.display = "none";

            productos.forEach((producto) => {
                producto.style.display = "";
            });

            return;
        }


        const totalPaginas =
            Math.ceil(
                productos.length / PRODUCTOS_POR_PAGINA
            );


        let paginaActual = 1;


        function mostrarPagina(numeroPagina) {

            paginaActual = numeroPagina;


            const inicio =
                (paginaActual - 1) *
                PRODUCTOS_POR_PAGINA;

            const fin =
                inicio +
                PRODUCTOS_POR_PAGINA;


            productos.forEach((producto, index) => {

                if (
                    index >= inicio &&
                    index < fin
                ) {

                    producto.style.display = "";

                } else {

                    producto.style.display = "none";

                }

            });


            construirControles();


            // Volver al comienzo de la categoría
            // al cambiar de página.
            categoria.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }


        function construirControles() {

            paginacion.innerHTML = "";


            // Botón ANTERIOR
            const anterior =
                document.createElement("button");

            anterior.type = "button";
            anterior.className = "store-pagination-button";
            anterior.textContent = "← ANTERIOR";

            anterior.disabled =
                paginaActual === 1;


            anterior.addEventListener(
                "click",
                () => {

                    if (paginaActual > 1) {
                        mostrarPagina(
                            paginaActual - 1
                        );
                    }

                }
            );


            paginacion.appendChild(anterior);


            // Números de página
            for (
                let numero = 1;
                numero <= totalPaginas;
                numero++
            ) {

                const boton =
                    document.createElement("button");

                boton.type = "button";

                boton.className =
                    "store-pagination-button";


                if (numero === paginaActual) {

                    boton.classList.add(
                        "active"
                    );

                }


                boton.textContent =
                    numero;


                boton.addEventListener(
                    "click",
                    () => {

                        if (
                            numero !== paginaActual
                        ) {

                            mostrarPagina(numero);

                        }

                    }
                );


                paginacion.appendChild(boton);

            }


            // Botón SIGUIENTE
            const siguiente =
                document.createElement("button");

            siguiente.type = "button";
            siguiente.className =
                "store-pagination-button";

            siguiente.textContent =
                "SIGUIENTE →";


            siguiente.disabled =
                paginaActual === totalPaginas;


            siguiente.addEventListener(
                "click",
                () => {

                    if (
                        paginaActual <
                        totalPaginas
                    ) {

                        mostrarPagina(
                            paginaActual + 1
                        );

                    }

                }
            );


            paginacion.appendChild(
                siguiente
            );

        }


        // Mostrar inicialmente la primera página.
        mostrarPagina(1);

    });

}


/* =========================================================
   INICIALIZACIÓN
   ========================================================= */

cargarVideos();

document.addEventListener(
    "DOMContentLoaded",
    () => {

        cargarNoticias();

        crearPaginacionTienda();

    }
);
