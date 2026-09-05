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
            enlace.href = `https://www.youtube.com/watch?v=${videoId}`;


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

        console.error("Error al cargar los vídeos:", error);

    }
}


cargarVideos();
