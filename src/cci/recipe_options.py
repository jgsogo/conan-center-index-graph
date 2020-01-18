
import json
import logging
import os
from itertools import product

from conans import tools

from cci.recipe import Recipe
from cci.run_conan import run_conan
from cci.utils import temp_file

log = logging.getLogger(__name__)


def pop_options(options):
    if isinstance(options, dict):
        options.pop('shared', None)
        options.pop('fPIC', None)
    elif isinstance(options, (tuple, list)):
        d = {}
        for it in options:
            k, v = it.split('=')
            d[k] = v
        options = pop_options(d)
    return options


def explode_options(recipe):
    assert not recipe.options, "Unexpected: recipe with options"

    with temp_file() as output_file:
        cmd = ['inspect', '-a', 'options', '--json', output_file, recipe.conanfile]
        run_conan(cmd)
        options = json.loads(tools.load(output_file))['options']
    options = pop_options(options)

    if options:
        opts_as_str = []
        for opt, values in options.items():
            # Try to enable as many things as possible to maximize dependencies
            if set(values) == set([True, False]):
                if any([it in opt for it in ['disable_', 'without_', 'no_']]):
                    opts_as_str.append(["{}=False".format(opt)])
                elif any([it in opt for it in ['enable_', 'with_']]):
                    opts_as_str.append(["{}=True".format(opt)])
                else:
                    #print(opt)
                    opts_as_str.append(["{}={}".format(opt, v) for v in values])

        for combination in product(*opts_as_str):
            yield Recipe(ref=recipe.ref, conanfile=recipe.conanfile, options=tuple(combination))

    with temp_file() as output_file:
        cmd = ['inspect', '-a', 'default_options', '--json', output_file, recipe.conanfile]
        run_conan(cmd)
        default_options = json.loads(tools.load(output_file))['default_options']
    default_options = pop_options(default_options)
    combination = ()
    if default_options:
        combination = ("{}={}".format(k, v) for k, v in default_options.items())
    yield Recipe(ref=recipe.ref, conanfile=recipe.conanfile, options=combination)


def explode_options_without_duplicates(recipe):
    recipes = list(explode_options(recipe))

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

    before = len(recipes)
    recipes = [x.obj for x in set(HashMyAttr(obj) for obj in recipes)]
    return recipes
