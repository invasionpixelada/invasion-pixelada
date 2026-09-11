/*
    INVASIÓN PIXELADA
    SCRIPT PRINCIPAL
*/


/* =========================================================
   VÍDEOS DE YOUTUBE
   ========================================================= */

const API_KEY = "AIzaSyAE_wqprOnVFSdGDb2-qMWqtkutgwfoHXQ";
const CHANNEL_HANDLE = "@invasionpixelada";


async function cargarVideos() {

    const tarjetas =
        document.querySelectorAll(".video-card");


    try {

        // -------------------------------------------------
        // 1. Obtener información del canal
        // -------------------------------------------------

        const channelResponse =
            await fetch(
                `https://www.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle=${encodeURIComponent(CHANNEL_HANDLE)}&key=${API_KEY}`
            );


        const channelData =
            await channelResponse.json();


        if (
            !channelData.items ||
            channelData.items.length === 0
        ) {

            throw new Error(
                "No se ha encontrado el canal."
            );

        }


        const uploadsPlaylistId =
            channelData.items[0]
                .contentDetails
                .relatedPlaylists
                .uploads;


        // -------------------------------------------------
        // 2. Obtener los 6 vídeos más recientes
        // -------------------------------------------------

        const videosResponse =
            await fetch(
                `https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId=${uploadsPlaylistId}&maxResults=6&key=${API_KEY}`
            );


        const videosData =
            await videosResponse.json();


        if (!videosData.items) {

            throw new Error(
                "No se han encontrado vídeos."
            );

        }


        // -------------------------------------------------
        // 3. Rellenar las tarjetas
        // -------------------------------------------------

        videosData.items.forEach(
            (video, index) => {

                if (!tarjetas[index]) {
                    return;
                }


                const snippet =
                    video.snippet;


                const videoId =
                    snippet.resourceId.videoId;


                const enlace =
                    tarjetas[index]
                        .querySelector(".video-link");


                const imagen =
                    tarjetas[index]
                        .querySelector(".video-placeholder");


                const titulo =
                    tarjetas[index]
                        .querySelector("h3");


                const informacion =
                    tarjetas[index]
                        .querySelector("p");


                // Enlace
                enlace.href =
                    `https://www.youtube.com/watch?v=${videoId}`;


                // Miniatura
                if (
                    snippet.thumbnails &&
                    snippet.thumbnails.high
                ) {

                    imagen.innerHTML = `
                        <img
                            src="${snippet.thumbnails.high.url}"
                            alt="${snippet.title}"
                            loading="lazy"
                        >
                    `;

                }


                // Título
                titulo.textContent =
                    snippet.title;


                // Fecha
                const fecha =
                    new Date(
                        snippet.publishedAt
                    );


                informacion.textContent =
                    fecha.toLocaleDateString(
                        "es-ES",
                        {
                            day: "numeric",
                            month: "long",
                            year: "numeric"
                        }
                    );

            }
        );


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


/*
    Número máximo de noticias que mostraremos.
*/

const NUMERO_NOTICIAS = 6;


/*
    Palabras relacionadas con Invasión Pixelada.

    El filtro se ha hecho deliberadamente más amplio que
    el anterior para que no desaparezcan noticias que sí
    pueden resultar interesantes para la temática de la web.
*/

const PALABRAS_NOTICIAS = [

    // Aventuras
    "aventura",
    "aventuras",
    "aventura gráfica",
    "aventura grafica",
    "point & click",
    "point and click",
    "point-and-click",

    // Narrativa
    "narrativa",
    "narrativo",
    "narración",
    "narracion",
    "historia",
    "histórico",
    "historico",
    "personaje",
    "personajes",

    // Misterio / terror
    "misterio",
    "misterioso",
    "terror",
    "horror",
    "lovecraft",
    "lovecraftiano",
    "thriller",
    "detective",
    "investigación",
    "investigacion",

    // Puzles
    "puzle",
    "puzles",
    "puzzle",
    "puzzles",
    "enigmas",
    "enigma",

    // Géneros relacionados
    "visual novel",
    "visual novels",
    "novela visual",
    "walking simulator",
    "walking simulators",

    // Ciencia ficción
    "ciencia ficción",
    "ciencia ficcion",
    "ciencia-ficción",
    "sci-fi",
    "science fiction",

    // Juegos narrativos / historias
    "historia interactiva",
    "juego narrativo",
    "juegos narrativos",
    "experiencia narrativa",

    // Análisis / reseñas
    "análisis",
    "analisis",
    "reseña",
    "reseñas",
    "review",

    // Algunos términos que aparecen habitualmente
    // en noticias de juegos que pueden interesarnos
    "indie",
    "metroidvania",
    "terror psicológico",
    "terror psicologico",
    "ficción",
    "ficcion"
];


/*
    Categorías que consideramos directamente relacionadas
    con la temática de la web.

    Esto permite que una noticia pueda entrar aunque
    el titular/descripción no contenga exactamente
    "aventura gráfica".
*/

const CATEGORIAS_RELEVANTES = [

    "aventuras",
    "aventura",
    "narrativa",
    "narrativo",
    "indie",
    "terror",
    "horror",
    "ps5",
    "pc",
    "multi",
    "switch",
    "switch2",
    "xbox"
];


/*
    Determina si una noticia es suficientemente relevante.
*/

function noticiaEsRelevante(noticia) {

    const titulo =
        String(
            noticia.title || ""
        ).toLowerCase();


    const descripcion =
        String(
            noticia.description || ""
        ).toLowerCase();


    const categoria =
        String(
            noticia.category || ""
        ).toLowerCase();


    const texto =
        `
        ${titulo}
        ${descripcion}
        ${categoria}
        `.toLowerCase();


    /*
        Primero comprobamos palabras directamente
        relacionadas con la temática.
    */

    const coincidencias =
        PALABRAS_NOTICIAS.filter(
            palabra =>
                texto.includes(
                    palabra.toLowerCase()
                )
        );


    if (coincidencias.length > 0) {
        return true;
    }


    /*
        Si es un análisis o reseña, también nos interesa.
    */

    if (
        titulo.includes("análisis") ||
        titulo.includes("analisis") ||
        titulo.includes("reseña") ||
        titulo.includes("review")
    ) {

        return true;

    }


    /*
        Si la categoría coincide con alguna categoría
        que consideramos válida.
    */

    if (
        CATEGORIAS_RELEVANTES.some(
            categoriaRelevante =>
                categoria === categoriaRelevante
        )
    ) {

        /*
            Para evitar que absolutamente cualquier
            noticia de una plataforma entre, exigimos
            además que tenga algún término relacionado
            con videojuegos o narrativa.
        */

        const terminosVideojuego = [

            "juego",
            "videojuego",
            "game",
            "gaming",
            "aventura",
            "análisis",
            "analisis",
            "reseña",
            "historia",
            "personaje",
            "puzle",
            "puzzle",
            "terror",
            "misterio",
            "indie",
            "metroidvania"

        ];


        if (
            terminosVideojuego.some(
                termino =>
                    texto.includes(termino)
            )
        ) {

            return true;

        }

    }


    return false;

}


/* =========================================================
   FECHAS DE NOTICIAS
   ========================================================= */

function formatearFechaNoticia(
    fechaOriginal
) {

    if (!fechaOriginal) {
        return "";
    }


    const fecha =
        new Date(
            fechaOriginal
        );


    if (
        Number.isNaN(
            fecha.getTime()
        )
    ) {

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


/* =========================================================
   IMAGEN DE NOTICIA
   ========================================================= */


/*
    El JSON puede utilizar distintos nombres para la imagen.

    Probamos todos ellos para que el sistema sea flexible.
*/

function obtenerImagenNoticia(noticia) {

    const posiblesImagenes = [

        noticia.image,
        noticia.imageUrl,
        noticia.imageURL,
        noticia.image_url,
        noticia.thumbnail,
        noticia.thumbnailUrl,
        noticia.thumbnail_url,
        noticia.enclosure,
        noticia.media,
        noticia.picture,
        noticia.cover

    ];


    for (
        const imagen of posiblesImagenes
    ) {

        if (
            typeof imagen === "string" &&
            imagen.trim() !== ""
        ) {

            return imagen;

        }


        /*
            Algunos RSS pueden devolver
            un objeto en enclosure.
        */

        if (
            imagen &&
            typeof imagen === "object"
        ) {

            if (
                typeof imagen.url === "string"
            ) {

                return imagen.url;

            }

        }

    }


    return "";

}


/* =========================================================
   CREAR TARJETA DE NOTICIA
   ========================================================= */

function crearTarjetaNoticia(
    noticia
) {

    const articulo =
        document.createElement(
            "article"
        );


    articulo.className =
        "news-card";


    /*
        Imagen
    */

    const imagen =
        obtenerImagenNoticia(
            noticia
        );


    if (imagen) {

        const contenedorImagen =
            document.createElement(
                "a"
            );


        contenedorImagen.className =
            "news-card-image";


        contenedorImagen.href =
            noticia.link || "#";


        contenedorImagen.target =
            "_blank";


        contenedorImagen.rel =
            "noopener noreferrer";


        const img =
            document.createElement(
                "img"
            );


        img.src =
            imagen;


        img.alt =
            noticia.title ||
            "Noticia";


        img.loading =
            "lazy";


        img.onerror =
            function () {

                contenedorImagen.classList.add(
                    "news-card-image-error"
                );

                img.style.display =
                    "none";

            };


        contenedorImagen.appendChild(
            img
        );


        articulo.appendChild(
            contenedorImagen
        );

    } else {

        /*
            Si todavía no tenemos imagen en noticias.json,
            dejamos un bloque visual para que la tarjeta
            no quede vacía.
        */

        const imagenFallback =
            document.createElement(
                "div"
            );


        imagenFallback.className =
            "news-card-image news-card-image-placeholder";


        imagenFallback.innerHTML = `
            <span>INVASIÓN<br>PIXELADA</span>
        `;


        articulo.appendChild(
            imagenFallback
        );

    }


    /*
        Contenido
    */

    const contenido =
        document.createElement(
            "div"
        );


    contenido.className =
        "news-card-content";


    /*
        Fuente
    */

    const fuente =
        document.createElement(
            "p"
        );


    fuente.className =
        "news-card-source";


    fuente.textContent =
        "uVeJuegos";


    contenido.appendChild(
        fuente
    );


    /*
        Categoría
    */

    if (
        noticia.category
    ) {

        const categoria =
            document.createElement(
                "p"
            );


        categoria.className =
            "news-card-category";


        categoria.textContent =
            noticia.category;


        contenido.appendChild(
            categoria
        );

    }


    /*
        Titular
    */

    const titulo =
        document.createElement(
            "h3"
        );


    titulo.textContent =
        noticia.title ||
        "Noticia";


    contenido.appendChild(
        titulo
    );


    /*
        Descripción
    */

    if (
        noticia.description
    ) {

        const descripcion =
            document.createElement(
                "p"
            );


        descripcion.className =
            "news-card-description";


        descripcion.textContent =
            noticia.description;


        contenido.appendChild(
            descripcion
        );

    }


    /*
        Fecha
    */

    const fecha =
        formatearFechaNoticia(
            noticia.pubDate
        );


    if (fecha) {

        const fechaElemento =
            document.createElement(
                "p"
            );


        fechaElemento.className =
            "news-card-date";


        fechaElemento.textContent =
            fecha;


        contenido.appendChild(
            fechaElemento
        );

    }


    /*
        Enlace
    */

    if (
        noticia.link
    ) {

        const enlace =
            document.createElement(
                "a"
            );


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


        contenido.appendChild(
            enlace
        );

    }


    articulo.appendChild(
        contenido
    );


    return articulo;

}


/* =========================================================
   CARGAR NOTICIAS
   ========================================================= */

async function cargarNoticias() {

    /*
        IMPORTANTE:
        El HTML utiliza #news-container.
    */

    const contenedor =
        document.querySelector(
            "#news-container"
        );


    if (!contenedor) {

        console.error(
            "No existe #news-container en el HTML."
        );

        return;

    }


    try {

        /*
            Cargamos noticias.json.
        */

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


        if (
            !Array.isArray(datos)
        ) {

            throw new Error(
                "El archivo noticias.json no contiene un array válido."
            );

        }


        console.log(
            "Noticias recibidas:",
            datos.length
        );


        /*
            Ordenamos por fecha, de más reciente
            a más antigua.
        */

        datos.sort(
            (
                a,
                b
            ) => {

                const fechaA =
                    new Date(
                        a.pubDate || 0
                    ).getTime();


                const fechaB =
                    new Date(
                        b.pubDate || 0
                    ).getTime();


                return fechaB - fechaA;

            }
        );


        /*
            Filtramos las noticias relevantes.
        */

        const noticiasRelevantes =
            datos
                .filter(
                    noticiaEsRelevante
                )
                .slice(
                    0,
                    NUMERO_NOTICIAS
                );


        console.log(
            "Noticias relevantes:",
            noticiasRelevantes.length
        );


        /*
            Si no hay ninguna, mostramos información
            para poder detectar fácilmente el problema.
        */

        if (
            noticiasRelevantes.length === 0
        ) {

            contenedor.innerHTML = `
                <div class="news-empty">
                    <p>
                        No hay noticias relacionadas
                        con nuestra temática en este momento.
                    </p>
                </div>
            `;

            return;

        }


        /*
            Limpiamos "Cargando noticias..."
        */

        contenedor.innerHTML = "";


        /*
            Creamos las tarjetas.
        */

        noticiasRelevantes.forEach(
            noticia => {

                const tarjeta =
                    crearTarjetaNoticia(
                        noticia
                    );


                contenedor.appendChild(
                    tarjeta
                );

            }
        );


    } catch (error) {

        console.error(
            "Error al cargar las noticias:",
            error
        );


        contenedor.innerHTML = `
            <div class="news-empty">
                <p>
                    No se han podido cargar las noticias
                    en este momento.
                </p>
            </div>
        `;

    }

}


/* =========================================================
   PAGINACIÓN DE LA TIENDA
   ========================================================= */

const PRODUCTOS_POR_PAGINA = 9;


function crearPaginacionTienda() {

    const categorias =
        document.querySelectorAll(
            ".store-category"
        );


    categorias.forEach(
        categoria => {

            const grid =
                categoria.querySelector(
                    ".store-grid"
                );


            const paginacion =
                categoria.querySelector(
                    ".store-pagination"
                );


            if (
                !grid ||
                !paginacion
            ) {

                return;

            }


            const productos =
                Array.from(
                    grid.children
                ).filter(
                    elemento =>
                        elemento.matches(
                            ".store-card"
                        )
                );


            /*
                Si no hay más de 9 productos,
                no necesitamos paginación.
            */

            if (
                productos.length <=
                PRODUCTOS_POR_PAGINA
            ) {

                paginacion.innerHTML =
                    "";


                paginacion.style.display =
                    "none";


                productos.forEach(
                    producto => {

                        producto.style.display =
                            "";

                    }
                );


                return;

            }


            const totalPaginas =
                Math.ceil(
                    productos.length /
                    PRODUCTOS_POR_PAGINA
                );


            let paginaActual = 1;


            function mostrarPagina(
                numeroPagina
            ) {

                paginaActual =
                    numeroPagina;


                const inicio =
                    (
                        paginaActual - 1
                    ) *
                    PRODUCTOS_POR_PAGINA;


                const fin =
                    inicio +
                    PRODUCTOS_POR_PAGINA;


                productos.forEach(
                    (
                        producto,
                        index
                    ) => {

                        if (
                            index >= inicio &&
                            index < fin
                        ) {

                            producto.style.display =
                                "";

                        } else {

                            producto.style.display =
                                "none";

                        }

                    }
                );


                construirControles();


                categoria.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }


            function construirControles() {

                paginacion.innerHTML =
                    "";


                /*
                    ANTERIOR
                */

                const anterior =
                    document.createElement(
                        "button"
                    );


                anterior.type =
                    "button";


                anterior.className =
                    "store-pagination-button";


                anterior.textContent =
                    "← ANTERIOR";


                anterior.disabled =
                    paginaActual === 1;


                anterior.addEventListener(
                    "click",
                    () => {

                        if (
                            paginaActual > 1
                        ) {

                            mostrarPagina(
                                paginaActual - 1
                            );

                        }

                    }
                );


                paginacion.appendChild(
                    anterior
                );


                /*
                    Números
                */

                for (
                    let numero = 1;
                    numero <= totalPaginas;
                    numero++
                ) {

                    const boton =
                        document.createElement(
                            "button"
                        );


                    boton.type =
                        "button";


                    boton.className =
                        "store-pagination-button";


                    if (
                        numero ===
                        paginaActual
                    ) {

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
                                numero !==
                                paginaActual
                            ) {

                                mostrarPagina(
                                    numero
                                );

                            }

                        }
                    );


                    paginacion.appendChild(
                        boton
                    );

                }


                /*
                    SIGUIENTE
                */

                const siguiente =
                    document.createElement(
                        "button"
                    );


                siguiente.type =
                    "button";


                siguiente.className =
                    "store-pagination-button";


                siguiente.textContent =
                    "SIGUIENTE →";


                siguiente.disabled =
                    paginaActual ===
                    totalPaginas;


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


            /*
                Primera página
            */

            mostrarPagina(1);

        }
    );

}


/* =========================================================
   INICIALIZACIÓN
   ========================================================= */


/*
    Vídeos
*/

cargarVideos();


/*
    Esperamos a que exista todo el HTML.
*/

document.addEventListener(
    "DOMContentLoaded",
    () => {

        cargarNoticias();

        crearPaginacionTienda();

    }
);
