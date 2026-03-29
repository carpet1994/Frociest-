from pythonforandroid.recipes.pygame import PygameRecipe


class Pygame261Recipe(PygameRecipe):
    version = "2.6.1"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"
    md5sum = None  # skip checksum so any mirror works


recipe = Pygame261Recipe()
