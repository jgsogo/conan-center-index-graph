import yaml
from conans import tools
import os
from collections import namedtuple

def get_profiles(profiles_dir):
    for it in os.listdir(profiles_dir):
        yield os.path.join(profiles_dir, it)
