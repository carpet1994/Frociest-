[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3,json

version = 0.1

# La recipe pygame custom in p4a_recipes/pygame/ forza pygame==2.6.1
# che non usa più longintrepr.h (rimosso in Python 3.11.10+).
requirements = python3,pygame,android,pyjnius

# Punta alla cartella con la recipe pygame custom (relativa a source.dir)
p4a.local_recipes = ./p4a_recipes

orientation = landscape
android.orientation = landscape
android.manifest.screenOrientation = sensorLandscape

fullscreen = 1

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET
android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34
android.archs = arm64-v8a


[buildozer]
log_level = 2
warn_on_root = 1
