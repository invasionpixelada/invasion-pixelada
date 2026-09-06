/*
    INVASIÓN PIXELADA
    VERSIÓN INTERNA: IP-JS-002
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

            const enlace = tarjetas[index].querySelector(".video-link");
            const imagen = tarjetas[index].querySelector(".video-placeholder");
            const titulo = tarjetas[index].querySelector("h3");
            const informacion = tarjetas[index].querySelector("p");


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
            const fecha = new Date(snippet.publishedAt);

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


                boton.textContent = numero;


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

        crearPaginacionTienda();

    }
);
