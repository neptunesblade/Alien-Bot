from Common.Mod import Mod


# Literally just an example mod
class ExampleMod(Mod):
    def __init__(self, mod_name, embed_color):
        super().__init__(mod_name, "Just an example mod.", {}, embed_color)
