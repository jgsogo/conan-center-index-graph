import os
import yaml
from conans import tools
from collections import defaultdict, namedtuple

Recipe = namedtuple("Recipe", ["ref", "conanfile", "options"])


def get_recipe_list(basepath):
    basepath = os.path.abspath(os.path.join(basepath, 'recipes'))
    
    for recipe in os.listdir(basepath):
        config = os.path.join(basepath, recipe, 'config.yml')
        if os.path.exists(config):
            data = yaml.safe_load(tools.load(config))
            for v, d in data["versions"].items():
                yield Recipe(ref="{}/{}".format(recipe, v), conanfile=os.path.join(basepath, recipe, d["folder"], 'conanfile.py'), options=None)
        else:
            for f in os.listdir(os.path.join(basepath, recipe)):
                yield Recipe(ref="{}/{}".format(recipe, f), conanfile=os.path.join(basepath, recipe, f, 'conanfile.py'), options=None)

def get_recipe_drafts(basepath):
    for recipe in os.listdir(basepath):
        name, _ = os.path.splitext(recipe)
        yield Recipe(ref="{}/{}".format(name, 'draft'), conanfile=os.path.join(basepath, recipe), options=None)
