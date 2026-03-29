[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3

version = 0.1

requirements = python3,pygame,android,pyjnius,pillow

orientation = landscape
android.orientation = landscape
android.manifest.screenOrientation = sensorLandscape

fullscreen = 1

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET
android.api = 34
android.minapi = 33
android.ndk = 25b
android.sdk = 34
android.archs = arm64-v8a, armeabi-v7a

# Forza p4a a usare un commit con la recipe pygame aggiornata
# (fix per longintrepr.h rimosso in Python 3.11+)
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1
