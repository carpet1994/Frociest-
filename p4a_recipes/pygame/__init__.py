"""
Recipe pygame custom: forza pygame 2.6.1 per evitare il bug longintrepr.h
presente in pygame <= 2.5.x con Python 3.11.10+.

Non importa la classe per nome (il nome varia tra versioni di p4a),
ma la recupera dinamicamente dal modulo originale.
"""
import importlib
import sys

# Carica il modulo originale della recipe pygame da p4a
_orig = importlib.import_module("pythonforandroid.recipes.pygame")

# Trova la classe Recipe definita nel modulo (convenzionalmente l'ultima
# sottoclasse di Recipe definita nel file, assegnata a `recipe`)
_base_recipe_cls = type(_orig.recipe)


class PygameFixedRecipe(_base_recipe_cls):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    md5sum = None  # disabilita checksum per compatibilità mirror


recipe = PygameFixedRecipe()
