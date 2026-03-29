[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3,json

version = 0.1

# pillow rimosso: non ha recipe p4a, fallisce la cross-compilazione arm64.
# Il codice gestisce già l'assenza con try/except ImportError nel load_gif().
# pygame viene incluso tramite la recipe p4a (develop branch) che usa pygame>=2.5
# e non dipende più dal rimosso longintrepr.h (rimosso in Python 3.11.15+)
requirements = python3,pygame,android,pyjnius

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

# Compila solo arm64 per tenere i tempi di build bassi.
# Aggiungere armeabi-v7a solo se serve supporto dispositivi molto vecchi.
android.archs = arm64-v8a


[buildozer]
log_level = 2
warn_on_root = 1
