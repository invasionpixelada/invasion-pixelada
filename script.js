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

    const tarjetas =
        document.querySelectorAll(".video-card");


    try {

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
            channelData
                .items[0]
                .contentDetails
                .relatedPlaylists
                .uploads;


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
                        .querySelector(
                            ".video-link"
                        );


                const imagen =
                    tarjetas[index]
                        .querySelector(
                            ".video-placeholder"
                        );


                const titulo =
                    tarjetas[index]
                        .querySelector("h3");


                const informacion =
                    tarjetas[index]
                        .querySelector("p");


                enlace.href =
                    `https://www.youtube.com/watch?v=${videoId}`;


                imagen.innerHTML = `
                    <img
                        src="${snippet.thumbnails.high.url}"
                        alt="${snippet.title}"
                        loading="lazy"
                    >
                `;


                titulo.textContent =
                    snippet.title;


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


const NUMERO_NOTICIAS = 6;



/*
    Palabras relacionadas con
    Invasión Pixelada.
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



/* =========================================================
   COMPROBAR RELEVANCIA
   ========================================================= */


function noticiaEsRelevante(
    noticia
) {

    const texto = `

        ${noticia.title || ""}

        ${noticia.description || ""}

        ${noticia.category || ""}

    `.toLowerCase();


    return PALABRAS_NOTICIAS.some(
        palabra =>
            texto.includes(
                palabra
            )
    );

}



/* =========================================================
   FECHA
   ========================================================= */


function formatearFechaNoticia(
    fechaOriginal
) {

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
   NOTICIAS
   ========================================================= */


async function cargarNoticias() {


    /*
        IMPORTANTE:

        En el HTML el contenedor se llama
        #news-container.

        Antes el JavaScript buscaba
        #news-grid y por eso había un
        problema.
    */


    const contenedor =
        document.querySelector(
            "#news-container"
        );


    if (!contenedor) {

        console.error(
            "No existe #news-container"
        );

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


        if (
            !Array.isArray(datos)
        ) {

            throw new Error(
                "El archivo noticias.json no tiene un formato válido."
            );

        }



        /*
            Filtrar noticias relevantes
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



        /*
            Si no hay noticias
        */

        if (
            noticiasRelevantes.length === 0
        ) {

            contenedor.innerHTML = `

                <p class="news-empty">

                    No hay noticias relacionadas
                    con nuestra temática
                    en este momento.

                </p>

            `;

            return;

        }



        /*
            Limpiar "Cargando noticias..."
        */

        contenedor.innerHTML = "";



        /*
            Crear tarjetas
        */

        noticiasRelevantes.forEach(
            noticia => {


                const articulo =
                    document.createElement(
                        "article"
                    );


                articulo.className =
                    "news-card";



                /* -------------------------------------
                   IMAGEN
                ------------------------------------- */


                if (
                    noticia.image
                ) {

                    const imagen =
                        document.createElement(
                            "img"
                        );


                    imagen.className =
                        "news-card-image";


                    imagen.src =
                        noticia.image;


                    imagen.alt =
                        noticia.title ||
                        "Noticia";


                    imagen.loading =
                        "lazy";


                    articulo.appendChild(
                        imagen
                    );

                }



                /* -------------------------------------
                   CONTENIDO
                ------------------------------------- */


                const contenido =
                    document.createElement(
                        "div"
                    );


                contenido.className =
                    "news-card-content";



                /* -------------------------------------
                   FUENTE
                ------------------------------------- */


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



                /* -------------------------------------
                   CATEGORÍA
                ------------------------------------- */


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



                /* -------------------------------------
                   TÍTULO
                ------------------------------------- */


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



                /* -------------------------------------
                   DESCRIPCIÓN
                ------------------------------------- */


                const descripcion =
                    document.createElement(
                        "p"
                    );


                descripcion.className =
                    "news-card-description";


                descripcion.textContent =
                    noticia.description ||
                    "";


                contenido.appendChild(
                    descripcion
                );



                /* -------------------------------------
                   FECHA
                ------------------------------------- */


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



                /* -------------------------------------
                   ENLACE
                ------------------------------------- */


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



                /* -------------------------------------
                   AÑADIR CONTENIDO
                ------------------------------------- */


                articulo.appendChild(
                    contenido
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

                No se han podido cargar
                las noticias en este momento.

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
                    (paginaActual - 1) *
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



            mostrarPagina(1);

        }
    );

}



/* =========================================================
   INICIALIZACIÓN
   ========================================================= */


document.addEventListener(
    "DOMContentLoaded",
    () => {

        cargarVideos();

        cargarNoticias();

        crearPaginacionTienda();

    }
);
