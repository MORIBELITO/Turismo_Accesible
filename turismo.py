import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import firebase_admin
from firebase_admin import credentials, auth, storage # Importa storage y auth
from firebase_admin.exceptions import FirebaseError # Importa para manejar errores específicos de Firebase
from werkzeug.utils import secure_filename # Para asegurar nombres de archivo seguros
import uuid # Para generar nombres de archivo únicos
from flask_cors import CORS # Importa CORS para permitir peticiones desde tu frontend

from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
# ¡IMPORTANTE! Cambia esto por una clave secreta fuerte y guárdala de forma segura.
# Puedes generar una con: import os; os.urandom(24).hex()
app.secret_key = 'tu_clave_secreta_super_secreta_aqui_cambiala_por_favor'

# Ruta a la carpeta de traducciones
TRANSLATIONS_DIR = os.path.join(app.root_path, 'translations')

# Cache de traducciones para evitar leer el archivo en cada request
TRANSLATIONS_CACHE = {}

def load_translations(lang):
    """
    Carga las traducciones para un idioma específico desde el archivo JSON.
    Cachéa los resultados para mejorar el rendimiento.
    """
    if lang not in TRANSLATIONS_CACHE:
        filepath = os.path.join(TRANSLATIONS_DIR, f'{lang}.json')
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    TRANSLATIONS_CACHE[lang] = json.load(f)
                print(f"Traducciones cargadas para: {lang}")
            except json.JSONDecodeError as e:
                print(f"Error JSON al cargar {filepath}: {e}")
                TRANSLATIONS_CACHE[lang] = {} # Fallback a diccionario vacío
            except FileNotFoundError:
                print(f"Archivo de traducción no encontrado: {filepath}")
                TRANSLATIONS_CACHE[lang] = {} # Fallback a diccionario vacío
            except Exception as e:
                print(f"Error inesperado al cargar {filepath}: {e}")
                TRANSLATIONS_CACHE[lang] = {} # Fallback a diccionario vacío
        else:
            print(f"Archivo de traducción no encontrado para el idioma: {lang} en {filepath}")
            TRANSLATIONS_CACHE[lang] = {} # Fallback a diccionario vacío
    return TRANSLATIONS_CACHE.get(lang, {})

@app.before_request
def before_request_func():
    """
    Se ejecuta antes de cada solicitud.
    Detecta, valida y establece el idioma actual para la solicitud.
    Carga las traducciones correspondientes y las hace disponibles globalmente (`g`).
    """
    supported_langs = ['es', 'en', 'qu', 'jp']
    default_lang = 'es'

    # 1. Intentar obtener el idioma de la URL (máxima prioridad)
    lang_from_url = request.args.get('lang')
    if lang_from_url in supported_langs:
        lang = lang_from_url
    else:
        # 2. Si no está en la URL o es inválido, intentar de la sesión
        if 'lang' in session and session['lang'] in supported_langs:
            lang = session['lang']
        else:
            # 3. Si no está en sesión, intentar de las cabeceras Accept-Language del navegador
            # y si no, usar el idioma por defecto
            lang = request.accept_languages.best_match(supported_langs)
            if not lang: # Si no hay coincidencia o cabecera
                lang = default_lang

    # Guardar el idioma final en la sesión para persistencia entre requests
    session['lang'] = lang
    
    # Hacer el idioma actual disponible para las vistas y plantillas
    g.current_lang = lang 
    
    # Cargar las traducciones para el idioma actual y hacerlas disponibles
    g.translations = load_translations(g.current_lang)
    print(f"Request procesada con idioma: {g.current_lang}")

def translate(text):
    """
    Función de traducción accesible en las plantillas Jinja.
    Busca el texto en el diccionario de traducciones del idioma actual.
    Si no se encuentra una traducción, devuelve el texto original.
    """
    return g.translations.get(text, text)

# Añade la función de traducción al entorno global de Jinja
app.jinja_env.globals['translate'] = translate
# Asegúrate de que url_for esté disponible globalmente también, aunque Flask lo hace por defecto
app.jinja_env.globals['url_for'] = url_for


# --- Rutas de la Aplicación ---

# Decorador que envuelve las rutas para manejar el parámetro <lang> en la URL
def localized_route(route_func):
    def wrapper(*args, **kwargs):
        # Extrae el idioma de la URL si está presente y lo pasa a g.current_lang
        # El before_request ya maneja la lógica principal, esto es para que las URLs con /<lang>/
        # actualicen g.current_lang en caso de que la URL la establezca explícitamente.
        lang_param = kwargs.get('lang')
        if lang_param and lang_param != g.current_lang:
            session['lang'] = lang_param
            g.current_lang = lang_param
            g.translations = load_translations(g.current_lang) # Recargar traducciones si cambia
        return route_func(*args, **kwargs)
    wrapper.__name__ = route_func.__name__ # Preserva el nombre de la función original
    return wrapper

@app.route('/')
@app.route('/<lang>/')
@localized_route
def principal(lang=None):
    return render_template('principal.html',
                           current_lang=g.current_lang,
                           active_page='principal')

@app.route('/<lang>/reviews')
@localized_route
def reseñas(lang):
    return render_template('reseñas.html',
                           current_lang=g.current_lang,
                           active_page='reseñas')

@app.route('/<lang>/about')
@localized_route
def acerca(lang):
    return render_template('acerca.html',
                           current_lang=g.current_lang,
                           active_page='acerca')

@app.route('/<lang>/contact')
@localized_route
def contacto(lang):
    return render_template('contacto.html',
                           current_lang=g.current_lang,
                           active_page='contacto')

@app.route('/<lang>/map')
@localized_route
def turismo(lang):
    return render_template('turismo.html',
                           current_lang=g.current_lang,
                           active_page='turismo')

@app.route('/<lang>/settings')
@localized_route
def configuracion(lang):
    # Aquí puedes añadir tu lógica para la página de configuración
    return render_template('configuracion.html',
                           current_lang=g.current_lang,
                           active_page='configuracion')

@app.route('/login')
@app.route('/<lang>/login')
@localized_route
def login(lang=None):
    return render_template('login.html',
                           current_lang=g.current_lang)

@app.route('/logout')
def logout():
    # Cierre de sesión de Firebase ya se maneja en el JS.
    # Si tuvieras sesión Flask, la limpiarías aquí:
    # session.clear()
    session.pop('lang', None) # Opcional: borrar el idioma de la sesión al cerrar sesión
    # Redirige a la página de login, manteniendo el idioma actual (si aún está disponible en 'g')
    return redirect(url_for('login', lang=getattr(g, 'current_lang', 'es')))

if __name__ == '__main__':
    app.run(debug=True, port=5000) # Puedes cambiar el puerto si lo necesitas
