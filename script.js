/*
    INVASIÓN PIXELADA
    VERSIÓN INTERNA: IP-JS-004
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
            titulo.textContent =
                snippet.title;


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

const NUMERO_NOTICIAS = 6;


/*
    Palabras y conceptos relacionados con el contenido
    de Invasión Pixelada.

    El filtro NO exige que aparezca una frase exacta como
    "aventura gráfica".

    Se busca cualquier relación razonable con:

    - Aventuras gráficas
    - Point & Click
    - Videojuegos narrativos
    - Visual novels
    - Walking simulators
    - Misterio
    - Terror
    - Horror
    - Lovecraft
    - Ciencia ficción
    - Thriller
    - Detectives
    - Investigación
    - Puzles
    - Historia
    - Narrativa
    - Juegos de autor
    - Indies narrativos
*/


const PALABRAS_NOTICIAS = [

    // Aventuras gráficas
    "aventura gráfica",
    "aventura grafica",
    "aventura",
    "aventuras gráficas",
    "aventuras graficas",

    // Point & Click
    "point & click",
    "point and click",
    "point-and-click",
    "point and click adventure",

    // Narrativa
    "narrativo",
    "narrativa",
    "narración",
    "narracion",
    "historia",
    "historias",
    "story",
    "story-driven",

    // Visual novels
    "visual novel",
    "visual novels",
    "novela visual",
    "novelas visuales",

    // Walking simulators
    "walking simulator",
    "walking simulators",

    // Misterio
    "misterio",
    "misterios",
    "misterioso",
    "misteriosa",

    // Terror
    "terror",
    "horror",
    "horrible",
    "horror psicológico",
    "horror psicologico",

    // Lovecraft
    "lovecraft",
    "lovecraftiano",
    "lovecraftiana",
    "mitos de cthulhu",
    "cthulhu",

    // Ciencia ficción
    "ciencia ficción",
    "ciencia ficcion",
    "sci-fi",
    "ciencia-ficción",
    "ciencia-ficcion",

    // Thriller
    "thriller",
    "suspense",

    // Investigación
    "detective",
    "detectives",
    "investigación",
    "investigacion",
    "investigar",
    "caso",
    "casos",

    // Puzles
    "puzle",
    "puzles",
    "puzzle",
    "puzzles",
    "rompecabezas",
    "enigmas",
    "enigma",

    // Personajes / investigación narrativa
    "protagonista",
    "protagonistas",

    // Géneros que pueden tener relación
    "metroidvania",
    "rol narrativo",
    "rpg narrativo",
    "juego narrativo",

    // Temáticas
    "realidad",
    "universo",
    "dimensiones",
    "memoria",
    "recuerdos",
    "misterio",
    "oculto",
    "oculta",

    // Desarrollo independiente
    "indie",
    "independiente",

    // Terror y ciencia ficción
    "monstruo",
    "monstruos",
    "criatura",
    "criaturas",
    "alien",
    "extraterrestre",
    "distopía",
    "distopia",
    "cyberpunk",
    "apocalipsis",
    "sobrenatural"

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
        palabra =>
            texto.includes(
                palabra.toLowerCase()
            )
    );

}


/*
    Calcula una puntuación para ordenar las noticias.

    Las palabras encontradas en el TÍTULO tienen más peso
    que las encontradas únicamente en la descripción.

    Esto permite que una noticia claramente relacionada
    aparezca antes que otra donde solamente se menciona
    una palabra relacionada de pasada.
*/

function puntuarNoticia(noticia) {

    const titulo =
        `${noticia.title || ""}`.toLowerCase();

    const descripcion =
        `${noticia.description || ""}`.toLowerCase();

    const categoria =
        `${noticia.category || ""}`.toLowerCase();


    let puntuacion = 0;


    PALABRAS_NOTICIAS.forEach(
        palabra => {

            const termino =
                palabra.toLowerCase();


            if (titulo.includes(termino)) {
                puntuacion += 5;
            }


            if (descripcion.includes(termino)) {
                puntuacion += 2;
            }


            if (categoria.includes(termino)) {
                puntuacion += 1;
            }

        }
    );


    /*
        Algunas palabras son especialmente importantes
        para nuestra temática.
    */

    const palabrasMuyRelevantes = [

        "aventura gráfica",
        "aventura grafica",
        "point & click",
        "point and click",
        "visual novel",
        "walking simulator",
        "narrativo",
        "narrativa",
        "misterio",
        "terror",
        "horror",
        "lovecraft",
        "puzle",
        "puzles",
        "puzzle",
        "puzzles"

    ];


    palabrasMuyRelevantes.forEach(
        palabra => {

            const termino =
                palabra.toLowerCase();


            if (titulo.includes(termino)) {
                puntuacion += 10;
            }


            if (descripcion.includes(termino)) {
                puntuacion += 4;
            }

        }
    );


    return puntuacion;

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

    /*
        IMPORTANTE:

        El HTML utiliza:

            id="news-container"

        Por eso aquí buscamos exactamente ese ID.
    */

    const contenedor =
        document.querySelector("#news-container");


    if (!contenedor) {

        console.error(
            "No se encuentra #news-container en el HTML."
        );

        return;

    }


    try {

        /*
            Añadimos un pequeño control de caché
            para que el navegador no utilice
            una versión antigua de noticias.json.
        */

        const respuesta =
            await fetch(
                "noticias.json?nocache=" +
                Date.now()
            );


        if (!respuesta.ok) {

            throw new Error(
                "No se ha podido cargar noticias.json. Código HTTP: " +
                respuesta.status
            );

        }


        const datos =
            await respuesta.json();


        if (!Array.isArray(datos)) {

            throw new Error(
                "El archivo noticias.json no tiene un formato válido."
            );

        }


        console.log(
            "Noticias recibidas:",
            datos.length
        );


        /*
            Filtramos las noticias relacionadas
            con la temática de la web.
        */

        let noticiasRelevantes =
            datos
                .filter(
                    noticia =>
                        noticiaEsRelevante(noticia)
                )
                .map(
                    noticia => ({
                        ...noticia,
                        puntuacion:
                            puntuarNoticia(noticia)
                    })
                );


        /*
            Ordenamos primero por puntuación
            y después por fecha.
        */

        noticiasRelevantes.sort(
            (a, b) => {

                if (
                    b.puntuacion !==
                    a.puntuacion
                ) {

                    return (
                        b.puntuacion -
                        a.puntuacion
                    );

                }


                const fechaA =
                    new Date(
                        a.pubDate
                    ).getTime();


                const fechaB =
                    new Date(
                        b.pubDate
                    ).getTime();


                return fechaB - fechaA;

            }
        );


        /*
            Nos quedamos con las primeras noticias.
        */

        noticiasRelevantes =
            noticiasRelevantes.slice(
                0,
                NUMERO_NOTICIAS
            );


        console.log(
            "Noticias relevantes:",
            noticiasRelevantes.length
        );


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
            Limpiamos el mensaje
            "Cargando noticias..."
        */

        contenedor.innerHTML = "";


        /*
            Creamos las tarjetas.
        */

        noticiasRelevantes.forEach(
            noticia => {

                const articulo =
                    document.createElement(
                        "article"
                    );


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
                    document.createElement(
                        "p"
                    );


                fuente.className =
                    "news-card-source";


                fuente.textContent =
                    "uVeJuegos";


                /*
                    Título
                */

                const titulo =
                    document.createElement(
                        "h3"
                    );


                titulo.textContent =
                    noticia.title ||
                    "Noticia";


                /*
                    Descripción
                */

                const descripcion =
                    document.createElement(
                        "p"
                    );


                descripcion.className =
                    "news-card-description";


                descripcion.textContent =
                    noticia.description ||
                    "";


                /*
                    Fecha
                */

                const fechaElemento =
                    document.createElement(
                        "p"
                    );


                fechaElemento.className =
                    "news-card-date";


                fechaElemento.textContent =
                    fecha;


                /*
                    Enlace
                */

                const enlace =
                    document.createElement(
                        "a"
                    );


                enlace.className =
                    "news-card-link";


                enlace.href =
                    noticia.link ||
                    "#";


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
        document.querySelectorAll(
            ".store-category"
        );


    categorias.forEach(
        (categoria) => {

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
                    (elemento) =>
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
                    (producto) => {

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
                        paginaActual -
                        1
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


                /*
                    Volver al comienzo de la categoría
                    al cambiar de página.
                */

                categoria.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }


            function construirControles() {

                paginacion.innerHTML =
                    "";


                /*
                    Botón ANTERIOR
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
                            paginaActual >
                            1
                        ) {

                            mostrarPagina(
                                paginaActual -
                                1
                            );

                        }

                    }
                );


                paginacion.appendChild(
                    anterior
                );


                /*
                    Números de página
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
                    Botón SIGUIENTE
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
                                paginaActual +
                                1
                            );

                        }

                    }
                );


                paginacion.appendChild(
                    siguiente
                );

            }


            /*
                Mostrar inicialmente
                la primera página.
            */

            mostrarPagina(1);

        }
    );

}


/* =========================================================
   INICIALIZACIÓN
   ========================================================= */

/*
    YouTube
*/

cargarVideos();


/*
    Esperamos a que el HTML esté cargado
    antes de buscar noticias y tienda.
*/

document.addEventListener(
    "DOMContentLoaded",
    () => {

        cargarNoticias();

        crearPaginacionTienda();

    }
);
