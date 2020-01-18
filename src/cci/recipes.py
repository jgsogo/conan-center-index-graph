import logging
import os
from typing import Optional, Iterator, List

import yaml
from conans import tools
from conans.model.ref import ConanFileReference

import cci.types
from cci.recipe_options import explode_options_without_duplicates
from cci.repository import Repository

from cci.recipe import Recipe

log = logging.getLogger(__name__)


def get_recipe_list(cci: Repository, cwd: cci.types.PATH, draft_folder: Optional[cci.types.PATH],
                    explode_options: bool = False) -> Iterator[Recipe]:
    # Clone the repo and return recipes in it
    folder = cci.clone(base_folder=cwd)
    recipes: List[str] = []
    for recipe in get_cci_recipe_list(folder):
        recipes.append(recipe.ref.name)
        if explode_options:
            for it in explode_options_without_duplicates(recipe):
                yield it
        else:
            yield recipe

    # Go for the draft recipes
    if draft_folder:
        for recipe in get_draft_recipes(draft_folder):
            if recipe.ref.name not in recipes:
                yield recipe


def get_cci_recipe_list(cci_folder: cci.types.PATH) -> Iterator[Recipe]:
    log.info(f"Gather recipes from {cci_folder}")

    recipes_folder = os.path.abspath(os.path.join(cci_folder, 'recipes'))
    for recipe in os.listdir(recipes_folder):
        config = os.path.join(recipes_folder, recipe, 'config.yml')
        if os.path.exists(config):
            data = yaml.safe_load(tools.load(config))
            for v, d in data["versions"].items():
                ref = ConanFileReference(name=recipe, version=str(v), user=None, channel=None)
                conanfile = os.path.join(recipes_folder, recipe, d["folder"], 'conanfile.py')
                yield Recipe(ref=ref, conanfile=conanfile)
        else:
            for f in os.listdir(os.path.join(recipes_folder, recipe)):
                ref = ConanFileReference(name=recipe, version=str(f), user=None, channel=None)
                conanfile = os.path.join(recipes_folder, recipe, f, 'conanfile.py')
                yield Recipe(ref=ref, conanfile=conanfile)


def get_draft_recipes(draft_folder: cci.types.PATH):
    log.info(f"Gather draft recipes from {draft_folder}")

    for recipe in os.listdir(draft_folder):
        name, _ = os.path.splitext(recipe)
        ref = ConanFileReference(name=name, version='draft', user=None, channel=None)
        conanfile = os.path.join(draft_folder, recipe)
        yield Recipe(ref=ref, conanfile=conanfile, is_draft=True)
