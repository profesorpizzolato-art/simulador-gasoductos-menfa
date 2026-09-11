# 1. Crear la carpeta del proyecto e ingresar a ella
mkdir simulador-gasoductos-menfa
cd simulador-gasoductos-menfa

# 2. Crear las subcarpetas de módulos, datos y configuración
mkdir .streamlit .github .github/workflows data modules
# Inicializar Git en la carpeta
git init

# Agregar todos los archivos creados
git add .

# Guardar el primer commit
git commit -m "feat: estructura e implementación inicial del simulador NAG-100"

# Cambiar la rama principal a main
git branch -M main

# Vincular con el repositorio de GitHub que creaste en el Paso 1
git remote add origin https://github.com/TU-USUARIO/simulador-gasoductos-menfa.git

# Subir los archivos
git push -u origin main
git add data/
git add app.py
git commit -m "feat: integración de base de datos JSON para preguntas y casos de inspección"
git push origin main
