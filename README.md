# JVA-Studio
JVA Studio: Elimina el fondo de cualquier imagen o GIF con IA. Genera imágenes desde texto usando Pollinations.ai. Incluye rotar, voltear, recortar y redimensionar. Interfaz moderna, guardado automático en carpetas. Código abierto.

## Cómo ejecutar

## 1. Instalar dependencias:
   
pip install -r requirements.txt

## 2. Ejecutar:

python main.py

O

## 🧩 Convertir el proyecto a .exe (Windows)

Este proyecto se puede convertir en un archivo ejecutable usando **PyInstaller**.

## 1. Instalar PyInstaller

pip install pyinstaller

## 2. Generar el ejecutable

pyinstaller --onefile --windowed --name="JVA_Studio" --icon=Assets/logo.ico --add-data "Assets;Assets" --copy-metadata pymatting --copy-metadata rembg --copy-metadata onnxruntime --hidden-import=tkinter --hidden-import=_tkinter --collect-all onnxruntime --collect-all rembg --collect-all pollinations --collect-all skimage --collect-all aiohttp --collect-all PIL main.py
