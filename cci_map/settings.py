import yaml
from conans import tools
from collections import namedtuple

Profile = namedtuple("Profile", ["os", "arch", "compiler", "compiler_version", "build_type"])

def get_profiles(settings_file, filter_pass_os=None):
    data = yaml.safe_load(tools.load(settings_file))
    for os in data['os']:
        for arch in data['arch']:
            for compiler, compiler_data in data['compiler'].items():
                if os == "Windows" and compiler != "Visual Studio": continue
                if os == "Linux" and compiler not in ["gcc", "clang"]: continue
                if os == "Macos" and compiler != "apple-clang": continue
                for compiler_version in compiler_data['version']:
                    for build_type in data['build_type']:
                        if filter_pass_os and os != filter_pass_os: continue
                        yield Profile(os=os, arch=arch, compiler=compiler, compiler_version=compiler_version, build_type=build_type)
