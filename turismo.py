import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import firebase_admin
from firebase_admin import credentials, auth, storage # Importa storage
from werkzeug.utils import secure_filename # Para asegurar nombres de archivo seguros

app = Flask(__name__)
# ¡IMPORTANTE! Cambia esto por una clave secreta fuerte y guárdala de forma segura.
# Puedes generar una con: import os; os.urandom(24).hex()
app.secret_key = os.environ.get('SECRET_KEY', 'AIzaSyARMkC0EBYElA8wVOpefSgMD4oADAIqD4o')

# Ruta a la carpeta de traducciones
TRANSLATIONS_DIR = os.path.join(app.root_path, 'translations')

# Cache de traducciones para evitar leer el archivo en cada request
TRANSLATIONS_CACHE = {}

# --- Configuración e inicialización de Firebase Admin SDK ---
# ATENCIÓN: Credenciales incrustadas directamente en el código.
# Esto NO es la mejor práctica de seguridad para producción.
# Se hace a petición explícita para simplificar el despliegue.
# Para un entorno de producción, se recomienda encarecidamente usar variables de entorno.
FIREBASE_SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "turismo-4e958",
  "private_key_id": "23e9c6e527d6584cecea454cc291d32bef57e91c",
  "private_key": """-----BEGIN PRIVATE KEY-----
MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCONCk8dKgzcleO
7ErRj9KjqKGCl+Pw6HAVrTGbaWC92W8cm9r1tT8+NpyiT/fhAIrzP35L+ii5Mf7B
EIrMR4X+JfxXxWAz3uwxL5Q6KScJRp7nOm3e6IeKoJbRhLXz9sMw0U8PrCUfhTk6
IpCaPjKdddZiz6frpVR8BjfDBNV/YZB5yz40r7zDpfg3VXswPs7wItgVXVaZyipn
vil1+fDyTu3qurpS5S1x+ysBzm/uwWwHpc/tIPV7nsJD/g22I3Vp9CDhwQBaGmPG
mehovGiaraG9h+uM7TE2nsny2ANlUtbMKBHmMY4ClXOLsLJOvtVjryRgV1OfGZGV
PHYo4C/bAgMBAAECggEABNJjhVd9h0EOoaoFCh0vPJ1pas7fPY+HrzR64T+DRLPX
MKvRIOAyq+XRuBLMUV9+AVbbJs20t1n+MIabg5G+oH+FrvQ3tfxVjQ5MZp4+m7kF
v63ioS/k2nWep5FqNnuHjYA2FTH2c9ebR2Drxk8j0uTMADFKYFpFeG8hGHg4mmPA
eMxb0EJVa6IPHvyV86FSaKtiPmAsX7tH0STCZVRRXrehvb6tevECKhH77HQYbxRn
G6pRN+CUjMHLly//Vkh8jlbuLY56ZfypiZQ4NtMfCL8mGBO59ckg6I6HsEHSsjJn
VSuqFN0mPnc5CA7X6zr1xKCA24VgSO3Fj9/kzw+OAQKBgQDA+QthFNm7GWMqGWsj
WVGtkyK8PcwcTlOWYyx/znbeeyzZgR7HF0sZFGB/fblZEUvnsUlyeheqeLjxugqu
NvZ/xsydD7rIL38CeOQyIEdsoNhwBN0IRe1sly/xXBrxiarh7n82YZZukQgFZ/cd
qKebo3CtqabLyHxG1PYNEne0swKBgQC8pi7y0C1qjVd62PuXgepi+iGq5Z/2uMOI
WLoCmqfHXRxK4mSW/Rtv3SBUCqI/dZSMUROcRmMzxBzDa70rKeWRHQSwxOSI9Sjz
oYbPon3vWEAHUIWVlhsN86uktZd0uRJg8mii7q21c+Rs/l0Dg462uf3vLzaLGwll
PJMUoCU8OQKBgGRtd+GXU1UO+k+/mMV1x4844rvqwV392XyLsm31SmGw4v9zNkxQ
sBGmTC4thRd4a/NxjZLZPZXHbCDJPKO8EP8gu/4FYKSsK0JjHgeESweakemCbnHO
yqhX6miHEbKgfeFFGMl5ciuqqOz/VVkHG+tg3NRUVWz6ssq+LCtTcB8HAoGAOPlz
um+3F7QiVH7N1V8uO8BRhLyfCDObEkXBv+GXhHWRguhG+vbsX2eISPmBMOtA9vPR
mWQEt/Clwzt5wVyA8ceyz/RXFSn9uT7yaSkpIa0kgVEHVzsjZp5OG4ugd2chrtfn
VDYDjoa22VglHVeRNYyMrb0zmuWKe+HEhfkr5bkCf1DhxYvQ+ss7g/a4qiH5u7qC
MJkbGWhxGZTmUaBUx/TJq5HRupgetD6NPf44keW51OGcRXk1PtqfyTa0DTB6vPoI
VLo3P/Dwyr9IEsd7SfARB1A2x2ZPi+CsS7pvJLqBs4pPWPMSrtW7F2px9DtZzN3T
A2DAP9BT8F4RxplCrzk=""",
  "client_email": "firebase-adminsdk-fbsvc@turismo-4e958.iam.gserviceaccount.com",
  "client_id": "118117002295102319140",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40turismo-4e958.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

try:
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_INFO)
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'turismo-4e958.appspot.com' # Reemplaza con el nombre de tu bucket de Firebase Storage
    })
    print("Firebase Admin SDK inicializado correctamente con credenciales incrustadas.")
except Exception as e:
    print(f"ERROR CRÍTICO: Fallo al inicializar Firebase Admin SDK con credenciales incrustadas: {e}")
    # En un entorno de producción, esto debería evitar que la aplicación se inicie
    # o al menos registrar un error severo.


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

# --- Nueva ruta para subir imágenes de perfil (Backend Proxy) ---
@app.route('/api/upload-profile-image', methods=['POST'])
def upload_profile_image():
    print("DEBUG: Recibida solicitud POST en /api/upload-profile-image")

    # Verifica si Firebase Admin SDK está inicializado
    if not firebase_admin._apps: # _apps es un diccionario que contiene las apps inicializadas
        print("ERROR: Firebase Admin SDK no está inicializado. No se puede subir el archivo.")
        return jsonify({"error": "El servidor no está configurado para subir archivos (Firebase no inicializado)."}), 500

    if 'profile_image' not in request.files:
        print("ERROR: 'profile_image' no encontrado en request.files.")
        return jsonify({"error": "No se encontró el archivo de imagen"}), 400

    file = request.files['profile_image']
    if file.filename == '':
        print("ERROR: Nombre de archivo vacío.")
        return jsonify({"error": "No se seleccionó ningún archivo"}), 400

    user_id = request.form.get('userId') # Obtenemos el userId enviado desde el frontend
    if not user_id:
        print("ERROR: ID de usuario no proporcionado en el formulario.")
        return jsonify({"error": "ID de usuario no proporcionado"}), 400

    if file:
        filename = secure_filename(file.filename)
        # Define la ruta en Firebase Storage: profile_images/{userId}/{nombre_archivo}
        blob_name = f"profile_images/{user_id}/{filename}"
        
        try:
            bucket = storage.bucket()
            blob = bucket.blob(blob_name)
            
            print(f"DEBUG: Intentando subir archivo '{filename}' a '{blob_name}' para el usuario '{user_id}'")
            blob.upload_from_file(file)
            print(f"DEBUG: Archivo '{filename}' subido exitosamente a Storage.")

            # Hacer el archivo público es crucial para que el frontend pueda acceder a él.
            # Asegúrate de que tus reglas de Firebase Storage permitan la lectura pública para esta ruta.
            blob.make_public()
            public_url = blob.public_url
            print(f"DEBUG: Archivo '{filename}' marcado como público. URL: {public_url}")

            # Opcional: Lógica para eliminar la imagen anterior del usuario
            # Si quieres implementar esto, el frontend debería enviar la `storagePath` anterior.
            # old_photo_path = request.form.get('oldPhotoPath')
            # if old_photo_path and old_photo_path != blob_name:
            #     try:
            #         old_blob = bucket.blob(old_photo_path)
            #         old_blob.delete()
            #         print(f"DEBUG: Imagen anterior eliminada: {old_photo_path}")
            #     except Exception as delete_error:
            #         print(f"ADVERTENCIA: Error al eliminar imagen anterior {old_photo_path}: {delete_error}")

            return jsonify({"success": True, "photoURL": public_url, "storagePath": blob_name}), 200
        except Exception as e:
            print(f"ERROR: Fallo al subir la imagen a Firebase Storage: {e}")
            return jsonify({"error": f"Error al subir la imagen: {str(e)}"}), 500
    
    print("ERROR: Condición de archivo inesperada (esto no debería ocurrir si 'file' es True).")
    return jsonify({"error": "Error desconocido al procesar la imagen"}), 500

# --- Ruta de prueba para verificar que el backend está vivo ---
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Backend is running", "firebase_initialized": firebase_admin._apps is not None}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000) # Puedes cambiar el puerto si lo necesitas
