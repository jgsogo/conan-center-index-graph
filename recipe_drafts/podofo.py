from conans import ConanFile


class Recipe(ConanFile):
    name = "podofo"

    settings = "os", "arch", "compiler", "build_type"

    def requirements(self):
        self.requires("fontconfig/draft")
