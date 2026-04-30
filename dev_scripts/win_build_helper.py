import os
import sys

# Este script actúa como un 'runtime hook' para PyInstaller en Windows.
# Se ejecuta ANTES de que inicie la aplicación para configurar el entorno de GTK.

def setup_gtk_env():
    # Verificamos si estamos corriendo desde el bundle empaquetado de PyInstaller
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
        
        # Configurar variables de entorno para que GTK encuentre sus librerías dinámicas, esquemas y recursos
        os.environ['GTK_DATA_PREFIX'] = base_dir
        os.environ['GTK_EXE_PREFIX'] = base_dir
        
        # Directorio de esquemas (GSettings)
        schemas_dir = os.path.join(base_dir, 'share', 'glib-2.0', 'schemas')
        if os.path.exists(schemas_dir):
            os.environ['GSETTINGS_SCHEMA_DIR'] = schemas_dir
        
        # Evita errores si no se encuentran esquemas de GSettings
        os.environ['GSETTINGS_BACKEND'] = 'memory'
        
        # Directorios de datos estándar
        share_dir = os.path.join(base_dir, 'share')
        if os.path.exists(share_dir):
            os.environ['XDG_DATA_DIRS'] = share_dir
            
        # Añadir las dependencias al PATH para que ctypes y las librerías DLL subyacentes las encuentren
        if sys.platform == 'win32':
            os.environ['PATH'] = base_dir + os.pathsep + os.environ.get('PATH', '')
            # En Python 3.8+ en Windows, las DLLs deben añadirse explícitamente
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(base_dir)
                    bin_dir = os.path.join(base_dir, 'bin')
                    if os.path.exists(bin_dir):
                        os.add_dll_directory(bin_dir)
                except Exception:
                    pass

if sys.platform == 'win32':
    setup_gtk_env()
