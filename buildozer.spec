[app]
title = Frociest Rumble
package.name = frociestRumble
package.domain = org.tappetovolante

author = Tappeto Volante

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,gif,ogg,mp3
source.include_patterns = Images/*.png,Images/Arena/*.png,Audio/*.ogg,Audio/*.mp3,PG/Preview/*.png,PG/Jules/*.gif,PG/Poz/*.gif,PG/Ruben/*.gif,icon.png

version = 0.1

requirements = python3,pygame_ce,android,pyjnius,pillow

orientation = landscape
android.orientation = landscape

fullscreen = 1

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
