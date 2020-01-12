from conans import ConanFile


class Recipe(ConanFile):
    name = "fontconfig"

    settings = "os", "arch", "compiler", "build_type"

    def requirements(self):
        self.requires("freetype/2.10.1")
        self.requires("expat/2.2.9")
        if self.settings.os == "Linux":
            self.requires("libuuid/1.0.3")
