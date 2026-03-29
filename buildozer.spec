[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3

version = 0.1

# pygame_sdl2 è la recipe nativa di python-for-android per pygame,
# compatibile con Python 3.11+ e NDK r25b.
requirements = python3,pygame_sdl2,android,pyjnius,pillow

orientation = landscape
android.orientation = landscape
android.manifest.screenOrientation = sensorLandscape

fullscreen = 1

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET
# Android 14 = API 34
android.api = 34
android.minapi = 33
android.ndk = 25b
android.sdk = 34
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
