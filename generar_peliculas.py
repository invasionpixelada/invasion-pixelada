# INVASIÓN PIXELADA — GENERADOR DE PELÍCULAS
# Versión interna: IP-MOVIEGEN-002
# Requiere el secreto TMDB_API_TOKEN en GitHub Actions.
from pathlib import Path
import re, os, html, requests
from difflib import SequenceMatcher
from docx import Document

DOCUMENTO = Path('tienda/Peliculas.docx')
TIENDA_HTML = Path('tienda.html')
API_URL = 'https://api.themoviedb.org/3/search/movie'
IMAGEN_BASE_URL = 'https://image.tmdb.org/t/p/w500'
API_TOKEN = os.environ.get('TMDB_API_TOKEN')
TIMEOUT = 20
MARCADOR_INICIO = '<!-- PELICULAS AUTOMÁTICAS: INICIO -->'
MARCADOR_FIN = '<!-- PELICULAS AUTOMÁTICAS: FIN -->'

CONSULTAS_CONOCIDAS = {
    'archive': ['Archive', 'Archive 2020'],
    'upgrade': ['Upgrade', 'Upgrade 2018'],
    'blade runner': ['Blade Runner', 'Blade Runner 1982'],
}


def comprobar_api_token():
    if not API_TOKEN:
        raise RuntimeError('No se ha encontrado TMDB_API_TOKEN. Comprueba el secreto de GitHub Actions.')


def normalizar_texto(texto):
    texto = html.unescape(texto or '').lower()
    texto = texto.replace('’', "'").replace('‘', "'").replace('´', "'")
    texto = re.sub(r'[¿?¡!]', '', texto)
    texto = re.sub(r'[-–—_:,;()/]+', ' ', texto)
    texto = texto.replace("'", '').replace(chr(34), '')
    return re.sub(r'\s+', ' ', texto).strip()


def calcular_similitud(a, b):
    a, b = normalizar_texto(a), normalizar_texto(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def detectar_formato(titulo):
    texto = normalizar_texto(titulo)
    for nombre, variantes in [('Blu-ray', ['blu-ray', 'blu ray', 'bluray']), ('DVD', ['dvd']), ('4K UHD', ['4k uhd', 'uhd', '4k'])]:
        if any(normalizar_texto(v) in texto for v in variantes):
            return nombre
    return None


def quitar_formato(titulo):
    patron = r'\s*[\[(]\s*(blu[\s-]?ray|dvd|4k\s*uhd|uhd|4k)\s*[\])]\s*$'
    return re.sub(r'\s+', ' ', re.sub(patron, '', titulo.strip(), flags=re.I)).strip()


def obtener_titulo_base(titulo):
    resultado = titulo.strip()
    expresiones = [
        r'\bilimitado\b', r'\blimited\s+edition\b', r'\bedici[oó]n\s+limitada\b',
        r"\bcollector'?s?\s+edition\b", r'\bedici[oó]n\s+coleccionista\b',
        r'\bspecial\s+edition\b', r'\bedici[oó]n\s+especial\b', r'\bdeluxe\s+edition\b',
        r'\bedici[oó]n\s+deluxe\b', r'\bmontaje\s+final\b', r'\bfinal\s+cut\b',
        r'\bmontaje\s+del\s+director\b', r'\bversi[oó]n\s+del\s+director\b',
        r"\bdirector'?s\s+cut\b", r'\bmontaje\s+extendido\b', r'\bversi[oó]n\s+extendida\b',
        r'\bextended\s+cut\b', r'\bsin\s+censura\b', r'\bsin\s+cortes\b', r'\buncut\b',
    ]
    for expresion in expresiones:
        resultado = re.sub(expresion, ' ', resultado, flags=re.I)
    resultado = quitar_formato(resultado)
    resultado = re.sub(r'\s+', ' ', resultado)
    resultado = re.sub(r'\s*[-–—:]\s*$', '', resultado)
    return resultado.strip(' -–—:()[]')


def detectar_edicion(titulo):
    texto = normalizar_texto(titulo)
    patrones = [
        ('final cut', ['montaje final', 'final cut']),
        ("director's cut", ['montaje del director', 'version del director', 'versión del director', "director's cut"]),
        ('extended cut', ['montaje extendido', 'version extendida', 'versión extendida', 'extended cut']),
        ('uncut', ['sin censura', 'sin cortes', 'uncut']),
        ('deluxe', ['deluxe', 'edicion deluxe', 'edición deluxe']),
        ('collector', ['collector', 'edicion coleccionista', 'edición coleccionista']),
        ('limited', ['limited', 'edicion limitada', 'edición limitada']),
        ('special edition', ['special edition', 'edicion especial', 'edición especial']),
    ]
    return [nombre for nombre, variantes in patrones if any(normalizar_texto(v) in texto for v in variantes)]


def leer_productos():
    document = Document(DOCUMENTO)
    productos, titulo_actual, enlace_actual = [], None, None
    for paragraph in document.paragraphs:
        texto = paragraph.text.strip()
        if not texto or texto.upper() == 'PELICULAS':
            continue
        if texto.startswith('Título:'):
            titulo_actual = texto.replace('Título:', '', 1).strip()
            enlace_actual = None
        elif texto.startswith('Enlace:'):
            enlace_actual = texto.replace('Enlace:', '', 1).strip()
        if titulo_actual and enlace_actual:
            sin_formato = quitar_formato(titulo_actual)
            productos.append({'titulo': titulo_actual, 'titulo_busqueda': sin_formato,
                              'titulo_base': obtener_titulo_base(sin_formato),
                              'ediciones': detectar_edicion(sin_formato),
                              'formato': detectar_formato(titulo_actual), 'enlace': enlace_actual})
            titulo_actual, enlace_actual = None, None
    return productos


def buscar_peliculas(titulo):
    respuesta = requests.get(API_URL,
        params={'query': titulo, 'include_adult': 'false', 'language': 'es-ES', 'page': 1},
        headers={'Authorization': f'Bearer {API_TOKEN}', 'accept': 'application/json'}, timeout=TIMEOUT)
    respuesta.raise_for_status()
    return respuesta.json().get('results', [])


def titulo_tmdb(pelicula):
    return pelicula.get('title') or pelicula.get('original_title') or ''


def anio_tmdb(pelicula):
    fecha = pelicula.get('release_date', '')
    return fecha[:4] if fecha else None


def puntuar(producto, pelicula):
    titulos_producto = [producto['titulo_busqueda'], producto['titulo_base']]
    titulos_pelicula = [pelicula.get('title', ''), pelicula.get('original_title', '')]
    similitud = max((calcular_similitud(a, b) for a in titulos_producto for b in titulos_pelicula if a and b), default=0.0)
    base = normalizar_texto(producto['titulo_base'])
    titulos = [normalizar_texto(pelicula.get('title', '')), normalizar_texto(pelicula.get('original_title', ''))]
    bonus_titulo = 0.0
    for candidato in titulos:
        if candidato and base:
            if candidato == base:
                bonus_titulo = max(bonus_titulo, 0.65)
            elif base in candidato or candidato in base:
                bonus_titulo = max(bonus_titulo, 0.20)
    objetivo = {'archive': '2020', 'upgrade': '2018', 'blade runner': '1982'}.get(base)
    bonus_anio = 0.25 if objetivo and anio_tmdb(pelicula) == objetivo else 0.0
    tiene_cartel = bool(pelicula.get('poster_path'))
    puntuacion = similitud + bonus_titulo + (0.12 if tiene_cartel else -0.15) + bonus_anio
    return {'pelicula': pelicula, 'titulo_tmdb': titulo_tmdb(pelicula), 'similitud': similitud,
            'puntuacion': puntuacion, 'tiene_cartel': tiene_cartel}


def seleccionar_pelicula(producto, peliculas):
    resultados = [puntuar(producto, p) for p in peliculas if titulo_tmdb(p)]
    if not resultados:
        return None
    resultados.sort(key=lambda r: r['puntuacion'], reverse=True)
    con_cartel = [r for r in resultados if r['tiene_cartel']]
    mejor = (con_cartel or resultados)[0]
    if mejor['similitud'] < 0.48 and not mejor['tiene_cartel']:
        return None
    return mejor


def crear_consultas(producto):
    base, busqueda = producto['titulo_base'].strip(), producto['titulo_busqueda'].strip()
    consultas = [busqueda]
    if base and normalizar_texto(base) != normalizar_texto(busqueda):
        consultas.append(base)
    base_normalizado = normalizar_texto(base)
    for clave, variantes in CONSULTAS_CONOCIDAS.items():
        if clave in base_normalizado:
            consultas.extend(variantes)
    salida, vistas = [], set()
    for consulta in consultas:
        clave = normalizar_texto(consulta)
        if clave and clave not in vistas:
            salida.append(consulta)
            vistas.add(clave)
    return salida


def buscar_cartel(producto):
    print(f"  - Producto: {producto['titulo']}")
    print(f"  - Título base: {producto['titulo_base']}")
    mejor_global, errores = None, []
    for consulta in crear_consultas(producto):
        print(f'  - Consultando TMDB: {consulta}')
        try:
            peliculas = buscar_peliculas(consulta)
        except requests.exceptions.RequestException as error:
            errores.append(f'{consulta}: {error}')
            print(f'    Error de TMDB: {error}')
            continue
        print(f'    Resultados devueltos: {len(peliculas)}')
        seleccionado = seleccionar_pelicula(producto, peliculas)
        if not seleccionado:
            print('    Sin candidato válido con cartel.')
            continue
        pelicula = seleccionado['pelicula']
        print(f"    Candidato: {seleccionado['titulo_tmdb']} ({anio_tmdb(pelicula) or 'año desconocido'}); similitud {seleccionado['similitud']:.2f}")
        if mejor_global is None or seleccionado['puntuacion'] > mejor_global['puntuacion']:
            mejor_global = seleccionado
        if seleccionado['similitud'] >= 0.70:
            break
    if not mejor_global:
        print('  No se ha encontrado cartel.' + ((' Errores: ' + ' | '.join(errores)) if errores else ''))
        return None
    pelicula = mejor_global['pelicula']
    poster_path = pelicula.get('poster_path')
    if not poster_path:
        print('  El candidato seleccionado no tiene poster_path.')
        return None
    cartel = IMAGEN_BASE_URL.rstrip('/') + '/' + poster_path.lstrip('/')
    print(f"  Cartel seleccionado: {mejor_global['titulo_tmdb']} ({anio_tmdb(pelicula) or 'año desconocido'})")
    print(f'  URL del cartel: {cartel}')
    return cartel


def generar_tarjeta(producto, imagen):
    titulo = html.escape(producto['titulo'])
    enlace = html.escape(producto['enlace'], quote=True)
    if imagen:
        imagen_html = f'''\n                            <img\n                                src="{html.escape(imagen, quote=True)}"\n                                alt="{titulo}"\n                                loading="lazy"\n                            >\n'''
    else:
        imagen_html = '''\n                            <div class="store-card-placeholder-inner">\n                                <span>IMAGEN NO DISPONIBLE</span>\n                            </div>\n'''
    return f'''\n                    <article class="store-card">\n                        <a href="{enlace}" target="_blank" rel="noopener noreferrer" class="store-card-image">\n{imagen_html}                        </a>\n                        <div class="store-card-content">\n                            <p class="store-card-label">RECOMENDADO</p>\n                            <h3>{titulo}</h3>\n                            <a href="{enlace}" target="_blank" rel="noopener noreferrer" class="store-card-link">VER EN AMAZON</a>\n                        </div>\n                    </article>\n'''


def actualizar_tienda(productos):
    contenido = TIENDA_HTML.read_text(encoding='utf-8')
    inicio, fin = contenido.find(MARCADOR_INICIO), contenido.find(MARCADOR_FIN)
    if inicio == -1 or fin == -1 or fin < inicio:
        raise RuntimeError('No se encuentran los marcadores de películas en tienda.html. No se ha modificado el archivo.')
    tarjetas = []
    for producto in productos:
        print(f"\nGenerando tarjeta: {producto['titulo']}")
        try:
            imagen = buscar_cartel(producto)
        except requests.exceptions.RequestException as error:
            print(f'  Error de conexión con TMDB: {error}')
            imagen = None
        except Exception as error:
            print(f'  Error inesperado buscando cartel: {error}')
            imagen = None
        tarjetas.append(generar_tarjeta(producto, imagen))
    bloque = MARCADOR_INICIO + '\n' + '\n'.join(tarjetas) + '\n                    ' + MARCADOR_FIN
    nuevo = contenido[:inicio] + bloque + contenido[fin + len(MARCADOR_FIN):]
    TIENDA_HTML.write_text(nuevo, encoding='utf-8')


def main():
    print('\n==============================================')
    print(' INVASIÓN PIXELADA — GENERADOR DE PELÍCULAS')
    print(' VERSIÓN: IP-MOVIEGEN-002')
    print('==============================================\n')
    comprobar_api_token()
    if not DOCUMENTO.exists():
        raise FileNotFoundError(f'No se encuentra {DOCUMENTO}')
    if not TIENDA_HTML.exists():
        raise FileNotFoundError(f'No se encuentra {TIENDA_HTML}')
    productos = leer_productos()
    print(f'Películas encontradas en el DOCX: {len(productos)}')
    if not productos:
        print('No hay películas que generar.')
        return
    actualizar_tienda(productos)
    print('\n✓ tienda.html actualizada con películas.\n')


if __name__ == '__main__':
    main()
