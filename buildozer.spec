[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3,json

# v0.5: animazioni crouch dedicate per Jules, Poz, Ruben e aggiunte le anteprime di Crimli e Refa
version = 0.5

# Nota: NON usare ffpyplayer (incompatibile con Cython 3).
# Le animazioni usano SheetAnimImage con sprite sheet PNG (definito in main.py).
requirements = python3,kivy,android,pyjnius

# Landscape
orientation = landscape
android.orientation = landscape
android.manifest.screenOrientation = sensorLandscape

fullscreen = 1

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET

# FIX AGGIORNAMENTO: stesso package.name + package.domain + versione crescente
# permette l'installazione come aggiornamento su versioni precedenti.
# android.numeric_version deve essere strettamente crescente ad ogni release.
android.numeric_version = 5

# Firma debug: Android permette aggiornamento solo se la firma è la stessa.
# In debug mode buildozer usa sempre la stessa debug keystore -> OK.

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
