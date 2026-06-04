[app]
title = Predictor Futebol
package.name = predictor_futebol
package.domain = org.meuapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Bibliotecas necessárias para o seu código e para conexões seguras com a API
requirements = python3, kivy, requests, urllib3, certifi

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
