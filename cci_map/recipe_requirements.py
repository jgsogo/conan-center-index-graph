from run_conan import run_conan
from conans import tools
import os
import logging
import json
from itertools import product
from cci_recipe_list import Recipe

log = logging.getLogger(__name__)


def get_requirements(recipe, profile):
    name, _ = recipe.ref.split('/')
    profile_cmd = ['-s', 'os={}'.format(profile.os),
                   '-s', 'arch={}'.format(profile.arch),
                   '-s', 'compiler={}'.format(profile.compiler),
                   '-s', 'compiler.version={}'.format(profile.compiler_version),
                   '-s', 'build_type={}'.format(profile.build_type),
                   ]

    options_cmd = []
    if recipe.options:
        for opt in recipe.options:
            options_cmd.extend(['-o', opt])

    output_file = os.path.join('.requirements', recipe.ref)
    cmd = ['info', '-db', '--json', output_file] + profile_cmd + options_cmd + [recipe.ref + '@']
    r = run_conan(cmd)
    if 'Invalid configuration' in r:
        return

    try:
        content = json.loads(tools.load(output_file))
        for it in content:
            if it['reference'] == recipe.ref:
                return it.get('requires', []), it.get('build_requires', [])
        
        assert False, "Never get here!"
    except Exception as e:
        log.error("Error!!! {}".format(e))
        log.error(r)

