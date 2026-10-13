# =========================================================
# INVASIÓN PIXELADA — GENERADOR DE VIDEOJUEGOS
# VERSIÓN INTERNA: IP-GAMEGEN-006
# =========================================================
from pathlib import Path
import os, re, html
import requests
from difflib import SequenceMatcher
from docx import Document

DOCUMENTO = Path("tienda/Videojuegos.docx")
TIENDA_HTML = Path("tienda.html")
API_URL = "https://api.thegamesdb.net/v1/Games/ByGameName"
IMAGES_URL = "https://api.thegamesdb.net/v1/Games/Images"
API_KEY = os.environ.get("THEGAMESDB_API_KEY")
TIMEOUT = 20
MARCADOR_INICIO = "<!-- VIDEOJUEGOS AUTOMÁTICOS: INICIO -->"
MARCADOR_FIN = "<!-- VIDEOJUEGOS AUTOMÁTICOS: FIN -->"
PLATAFORMAS = [
    ("Sony Playstation 5", ["ps5", "playstation 5", "playstation5", "sony playstation 5"], "4980"),
    ("Sony Playstation 4", ["ps4", "playstation 4", "playstation4", "sony playstation 4"], "4919"),
    ("Nintendo Switch", ["nintendo switch", "switch"], "4971"),
    ("Xbox Series X/S", ["xbox series x/s", "xbox series x", "xbox series s"], "4981"),
    ("Xbox One", ["xbox one"], "4920"),
    ("PC", ["pc", "windows"], "1"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36"}

def comprobar_api_key():
    if not API_KEY:
        raise RuntimeError("No se ha encontrado THEGAMESDB_API_KEY.")

def normalizar_texto(texto):
    texto = html.unescape(str(texto or "")).lower().replace("’", "'").replace("‘", "'").replace("´", "'")
    texto = re.sub(r"[¿?¡!]", "", texto)
    texto = re.sub(r"[-–—_:,;()/]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

def similitud(a, b):
    a, b = normalizar_texto(a), normalizar_texto(b)
    return 1.0 if a == b else SequenceMatcher(None, a, b).ratio()

def detectar_plataforma(titulo):
    texto = normalizar_texto(titulo)
    for nombre, variantes, _ in PLATAFORMAS:
        for v in sorted(variantes, key=len, reverse=True):
            if re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", texto):
                return nombre, v
    return None, None

def quitar_plataforma(titulo, variante):
    if not variante: return titulo.strip()
    return re.sub(r"\s*[-–—:]?\s*" + re.escape(variante) + r"\s*$", "", titulo, flags=re.I).strip()

def nombre_base(titulo):
    s = re.sub(r"\s*[\[(].*?(edition|edición|deluxe|collector|collectors|limited|special|ultimate|gold|complete|definitive|game of the year|goty).*?[\])]", "", titulo, flags=re.I)
    s = re.sub(r"\s*[-–—:]\s*(deluxe|collector'?s?|limited|special|ultimate|gold|complete|definitive)\s+edition\s*$", "", s, flags=re.I)
    s = re.sub(r"\s*[-–—:]\s*25th\s+anniversary\s+edition\s*$", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip(" -–—:")

def leer_productos():
    productos, titulo, enlace = [], None, None
    for p in Document(DOCUMENTO).paragraphs:
        t = p.text.strip()
        if t.startswith("Título:"): titulo = t[len("Título:"):].strip()
        elif t.startswith("Enlace:"): enlace = t[len("Enlace:"):].strip()
        if titulo and enlace:
            plataforma, variante = detectar_plataforma(titulo)
            juego = quitar_plataforma(titulo, variante)
            productos.append({"titulo": titulo, "titulo_juego": juego, "titulo_base": nombre_base(juego), "plataforma": plataforma, "enlace": enlace})
            titulo = enlace = None
    return productos

def buscar_juegos(titulo, plataforma):
    params = {"apikey": API_KEY, "name": titulo, "fields": "platform", "include": "platform", "page": 1}
    for nombre, variantes, pid in PLATAFORMAS:
        if plataforma == nombre:
            params["filter[platform]"] = pid
            break
    r = requests.get(API_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("data", {}).get("games", []) or []

def obtener_imagenes(game_id):
    r = requests.get(IMAGES_URL, params={"apikey": API_KEY, "games_id": str(game_id), "filter[type]": "boxart"}, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json().get("data", {})
    base = data.get("base_url", {})
    if isinstance(base, dict): base = base.get("original") or base.get("large") or base.get("medium")
    if not base: return []
    images = data.get("images", {})
    listas = images.values() if isinstance(images, dict) else ([images] if isinstance(images, list) else [])
    out = []
    for lista in listas:
        if not isinstance(lista, list): continue
        for im in lista:
            if not isinstance(im, dict): continue
            side, typ = str(im.get("side", "")).lower(), str(im.get("type", "")).lower()
            if typ and typ != "boxart": continue
            if side and side not in ("front", "front boxart"): continue
            filename = im.get("filename")
            if filename:
                url = base.rstrip("/") + "/" + str(filename).lstrip("/")
                if url not in out: out.append(url)
    return out

def imagen_desde_amazon(enlace):
    # Alternativa automática: intenta leer la imagen principal de la página Amazon.
    try:
        r = requests.get(enlace, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        r.raise_for_status()
        page = r.text
        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'"hiRes"\s*:\s*"([^"]+)"',
            r'"large"\s*:\s*"([^"]+)"',
        ]
        for pattern in patterns:
            m = re.search(pattern, page, re.I)
            if m:
                url = html.unescape(m.group(1)).replace("\\u0026", "&").replace("\\/", "/")
                if url.startswith("https://") and ("amazon" in url.lower() or re.search(r"\.(jpg|jpeg|png)(\?|$)", url, re.I)):
                    print("  ✓ Imagen recuperada desde la página de Amazon.")
                    return url
        print("  - Amazon no expuso una imagen legible automáticamente.")
    except requests.RequestException as e:
        print(f"  - No se pudo consultar Amazon: {e}")
    return None

def buscar_portada(producto):
    print(f"  - Buscando {producto['titulo_juego']} ({producto['plataforma'] or 'plataforma no detectada'})")
    consultas = []
    for n in (producto["titulo_juego"], producto["titulo_base"]):
        if n and all(normalizar_texto(n) != normalizar_texto(x) for x in consultas): consultas.append(n)
    base = producto["titulo_base"]
    for sep in (":", " - ", " – "):
        if sep in base:
            n = base.split(sep, 1)[0].strip()
            if n and all(normalizar_texto(n) != normalizar_texto(x) for x in consultas): consultas.append(n)
    candidatos, vistos = [], set()
    for q in consultas:
        try: juegos = buscar_juegos(q, producto["plataforma"])
        except requests.RequestException as e:
            print(f"  - Error en TheGamesDB: {e}"); continue
        for juego in juegos:
            nombre = juego.get("game_title") or juego.get("name") or ""
            if not nombre: continue
            score = similitud(producto["titulo_juego"], nombre)
            umbral = 0.50 if normalizar_texto(q) == normalizar_texto(producto["titulo_base"]) else 0.65
            if score < umbral: continue
            gid = juego.get("id")
            if gid is None or str(gid) in vistos: continue
            vistos.add(str(gid)); candidatos.append((score, nombre, gid))
    candidatos.sort(reverse=True)
    for score, nombre, gid in candidatos:
        print(f"  - Candidato TheGamesDB: {nombre} (ID {gid}, coincidencia {score:.0%})")
        try: imgs = obtener_imagenes(gid)
        except requests.RequestException as e:
            print(f"  - Error consultando imágenes: {e}"); continue
        if imgs:
            print("  ✓ Portada encontrada en TheGamesDB.")
            return imgs[0]
    print("  - Sin portada válida en TheGamesDB; probando Amazon.")
    return imagen_desde_amazon(producto["enlace"])

def generar_tarjeta(producto, imagen):
    titulo = html.escape(producto["titulo"])
    enlace = html.escape(producto["enlace"], quote=True)
    if imagen:
        imagen_html = f'<img src="{html.escape(imagen, quote=True)}" alt="{titulo}" loading="lazy">'
    else:
        imagen_html = '<div class="store-card-placeholder-inner"><span>IMAGEN NO DISPONIBLE</span></div>'
    return f'''
                    <article class="store-card">
                        <a href="{enlace}" target="_blank" rel="noopener noreferrer" class="store-card-image">
                            {imagen_html}
                        </a>
                        <div class="store-card-content">
                            <p class="store-card-label">RECOMENDADO</p>
                            <h3>{titulo}</h3>
                            <a href="{enlace}" target="_blank" rel="noopener noreferrer" class="store-card-link">VER EN AMAZON</a>
                        </div>
                    </article>
'''

def actualizar_tienda(productos):
    contenido = TIENDA_HTML.read_text(encoding="utf-8")
    inicio, fin = contenido.find(MARCADOR_INICIO), contenido.find(MARCADOR_FIN)
    if inicio < 0 or fin < inicio:
        raise RuntimeError("No se encuentran los marcadores automáticos de videojuegos en tienda.html.")
    tarjetas = []
    for p in productos:
        print(f"\nGenerando tarjeta: {p['titulo']}")
        try: img = buscar_portada(p)
        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            print(f"  ✗ Error buscando portada: {e}"); img = None
        tarjetas.append(generar_tarjeta(p, img))
    bloque = MARCADOR_INICIO + "\n" + "\n".join(tarjetas) + "\n                    " + MARCADOR_FIN
    TIENDA_HTML.write_text(contenido[:inicio] + bloque + contenido[fin + len(MARCADOR_FIN):], encoding="utf-8")

def main():
    print("\nINVASIÓN PIXELADA — GENERADOR DE VIDEOJUEGOS IP-GAMEGEN-006\n")
    comprobar_api_key()
    if not DOCUMENTO.exists(): raise FileNotFoundError(f"No se encuentra {DOCUMENTO}")
    if not TIENDA_HTML.exists(): raise FileNotFoundError(f"No se encuentra {TIENDA_HTML}")
    productos = leer_productos()
    print(f"Videojuegos encontrados: {len(productos)}")
    if productos: actualizar_tienda(productos)
    print("\n✓ Proceso terminado.\n")

if __name__ == "__main__":
    main()
