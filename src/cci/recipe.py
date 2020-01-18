import json
import os
from dataclasses import dataclass
from itertools import product
from typing import Optional, Tuple

from conans import tools
from conans.model.ref import ConanFileReference

from cci import types
from cci.run_conan import ConanWrapper
from cci.utils import temp_file


@dataclass
class Recipe:
    ref: ConanFileReference
    conanfile: str
    options: Optional[tuple] = None
    is_draft: bool = False
    is_proxy: bool = False

    @property
    def ref_str(self):
        return f"{self.ref.name}-{self.ref.version}"

    def options_attrs(self) -> Tuple[dict, dict]:
        # Return options attribute and default_options as dictionary
        with temp_file() as json_file:
            cmd = ['inspect', '-a', 'options', '-a', 'default_options', '--json', json_file, self.conanfile]
            ConanWrapper().run(cmd)
            data = json.loads(tools.load(json_file))
        options, default_options = data['options'], data['default_options']

        def _normalize_as_dict(options_):
            if isinstance(options_, dict):
                pass
            elif isinstance(options_, (tuple, list)):
                d = dict(it.split('=') for it in options_)
                options_ = _normalize_as_dict(d)
            return options_

        return _normalize_as_dict(options) or {}, _normalize_as_dict(default_options) or {}

    def requirements(self, profile: types.PATH, log) -> Tuple[Optional[list], Optional[list]]:
        options_cmd = []
        if self.options:
            for opt in self.options:
                options_cmd.extend(['-o', opt])

        with temp_file() as output_file:
            cmd = ['graph', 'lock', '--build', '--profile', profile, '--lockfile', output_file]\
                  + options_cmd + [self.ref + '@']

            try:
                r = ConanWrapper().run(cmd)

                if 'Invalid configuration' in r:
                    log.warning(r)
                    return None, None

                content = json.loads(tools.load(output_file))
                for _, node in content['graph_lock']['nodes'].items():
                    ref, _ = ConanFileReference.loads(node['pref'].split('#'))
                    if ref == self.ref:
                        reqs = [k.split('#', 1)[0] for k, _ in node.get('requires', {}).items()]
                        breqs = [k.split('#', 1)[0] for k, _ in node.get('build_requires', {}).items()]
                        return reqs, breqs

                assert False, "Never get here!"
            except Exception as e:
                log.error(f"Error!!! {e}")
                log.error(f" - recipe: {self.ref}")
                log.error(f" - profile: {os.path.basename(profile)}")
                log.error(r)
        return None, None


def explode_options(recipe):
    if recipe.options:
        raise RuntimeError(f"Recipe {recipe.ref.name} has already options exploded")

    # Populate the options with those which can add/remove dependencies
    options, default_options = recipe.options_attrs()
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
        combination = ("{}={}".format(k, v) for k, v in default_options.items())
    yield Recipe(ref=recipe.ref, conanfile=recipe.conanfile, options=combination,
                 is_draft=recipe.is_draft, is_proxy=recipe.is_proxy)


def explode_options_without_duplicates(recipe):
    recipes = explode_options(recipe)

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
