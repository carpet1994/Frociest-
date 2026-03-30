"""
Recipe pygame custom: usa il sdist PyPI di pygame 2.6.1 invece del
tarball GitHub. Il sdist contiene i file .c già generati da Cython,
quindi la build NON richiede Cython nell'hostpython.

Problema risolto: quando si scarica pygame da GitHub (archive/{version}.tar.gz)
i file .pyx Cython sono presenti ma i .c pre-generati no, quindi
setup.py chiama cython per rigenerarli. Il sdist PyPI invece include
già i .c, e setup.py li usa direttamente (USE_CYTHON=0 implicito).
"""
import importlib

_orig = importlib.import_module("pythonforandroid.recipes.pygame")
_base_recipe_cls = type(_orig.recipe)


class PygameSdistRecipe(_base_recipe_cls):
    version = "2.6.1"
    # sdist da PyPI: contiene i .c pre-generati, NO Cython richiesto
    url = "https://files.pythonhosted.org/packages/source/p/pygame/pygame-{version}.tar.gz"
    md5sum = None  # disabilita checksum


recipe = PygameSdistRecipe()
