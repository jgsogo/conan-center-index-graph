import logging
import os
from itertools import product
from typing import Iterator, List
from typing import Optional

from conans.model.ref import ConanFileReference

import cci.types
from cci.recipe import Recipe
from cci.repository import Repository

log = logging.getLogger(__name__)


def get_recipe_list(cci_repo: Repository,
                    cwd: cci.types.PATH,
                    draft_folder: Optional[cci.types.PATH]) -> Iterator[Recipe]:
    # Clone the repo and return recipes in it
    cci_repo.clone(base_folder=cwd)
    recipes: List[str] = []
    for recipe in cci_repo.get_recipe_list():
        recipes.append(recipe.ref.name)
        yield recipe

    # Go for the draft recipes (avoid duplicates)
    if draft_folder:
        for recipe in get_draft_recipes(draft_folder):
            if recipe.ref.name not in recipes:
                yield recipe
            else:
                log.warning(f"Duplicate recipe in drafts: {recipe.ref.name}")


def get_draft_recipes(draft_folder: cci.types.PATH):
    log.info(f"Gather draft recipes from {draft_folder}")

    for recipe in os.listdir(draft_folder):
        name, _ = os.path.splitext(recipe)
        ref = ConanFileReference(name=name, version='draft', user=None, channel=None)
        conanfile = os.path.join(draft_folder, recipe)
        recipe = Recipe(ref=ref, conanfile=conanfile, is_draft=True)
        yield recipe


def _normalize_as_dict(options_):
    if isinstance(options_, dict):
        pass
    elif isinstance(options_, (tuple, list)):
        d = dict(it.split('=') for it in options_)
        options_ = _normalize_as_dict(d)
    return options_


def explode_shared_option(recipe, conan):
    options, default_options = conan.inspect(recipe, ['options', 'default_options'])
    options, default_options = _normalize_as_dict(options), _normalize_as_dict(default_options)
    if options and 'shared' in options:
        for it in options['shared']:
            yield Recipe(ref=recipe.ref, conanfile=recipe.conanfile, options=(f"shared={it}",),
                         is_draft=recipe.is_draft, is_proxy=recipe.is_proxy)
    else:
        yield recipe


def explode_options(recipe, conan):
    if recipe.options:
        raise RuntimeError(f"Recipe {recipe.ref.name} has already options exploded")

    # Populate the options with those which can add/remove dependencies
    options, default_options = conan.inspect(recipe, ['options', 'default_options'])
    options, default_options = _normalize_as_dict(options), _normalize_as_dict(default_options)
    for it in ['shared', 'fPIC']:
        options.pop(it, None)
        default_options.pop(it, None)

    # Combinations of all option values
    if options:
        opts_as_str = []
        for opt, values in options.items():
            # Try to enable as many things as possible to maximize dependencies
            if set(values) == {True, False}:
                if any([it in opt for it in ['disable_', 'without_', 'no_']]):
                    opts_as_str.append(["{}=False".format(opt)])
                elif any([it in opt for it in ['enable_', 'with_']]):
                    opts_as_str.append(["{}=True".format(opt)])
                else:
                    opts_as_str.append(["{}={}".format(opt, v) for v in values])

        for combination in product(*opts_as_str):
            yield Recipe(ref=recipe.ref, conanfile=recipe.conanfile, options=tuple(combination),
                         is_draft=recipe.is_draft, is_proxy=recipe.is_proxy)

    # Use default options (always)
    combination = ()
    if default_options:
        combination = tuple("{}={}".format(k, v) for k, v in default_options.items())
    yield Recipe(ref=recipe.ref, conanfile=recipe.conanfile, options=combination,
                 is_draft=recipe.is_draft, is_proxy=recipe.is_proxy)


def explode_options_without_duplicates(recipe, conan):
    recipes = explode_options(recipe, conan)

    class HashMyAttr:
        cmp_opts = None

        def __init__(self, obj):
            self.obj = obj
            if self.obj.options:
                self.cmp_opts = tuple(sorted(self.obj.options))

        def __hash__(self):
            return hash(self.cmp_opts)

        def __eq__(self, other):
            return self.cmp_opts == other.cmp_opts

    for x in set(HashMyAttr(obj) for obj in recipes):
        yield x.obj
