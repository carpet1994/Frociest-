[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3,json

version = 0.1

# FIX ANIMAZIONI GIF: aggiungere ffpyplayer come image provider per i GIF.
# "kivy" da solo non carica i GIF animati su Android.
# ffpyplayer è il provider ufficiale Kivy per video e GIF animati.
requirements = python3,kivy,android,pyjnius,ffpyplayer

# Forza ffpyplayer come provider per i video/gif (Kivy lo usa automaticamente
# se presente, ma esplicitarlo evita che venga saltato in alcune build)
android.add_aars =

# FIX LANDSCAPE: queste tre righe insieme garantiscono il landscape su Android.
# - orientation nel [app] imposta il manifest AndroidManifest.xml
# - android.manifest.screenOrientation lo rinforza nel tag <activity>
# - android.orientation è il vecchio campo buildozer (compatibilità)
orientation = landscape
android.orientation = landscape
android.manifest.screenOrientation = sensorLandscape

fullscreen = 1

icon.filename = %(source.dir)s/icon.png

# Permessi necessari
android.permissions = INTERNET

android.api = 34
android.minapi = 21
android.ndk = 25b
android.sdk = 34
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
