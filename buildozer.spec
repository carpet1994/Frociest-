[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3,json

version = 0.1

# ffpyplayer RIMOSSO: non compila con Cython 3.
# Le animazioni usano SheetAnimImage (sprite sheet PNG) definito in main.py.
requirements = python3,kivy,android,pyjnius

# Landscape: tutte e tre le righe sono necessarie insieme.
orientation = landscape
android.orientation = landscape
android.manifest.screenOrientation = sensorLandscape

fullscreen = 1

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
