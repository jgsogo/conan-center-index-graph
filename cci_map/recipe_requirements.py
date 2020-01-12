from run_conan import run_conan
from conans import tools
import os
import logging
import json
from itertools import product
from cci_recipe_list import Recipe

#log = logging.getLogger(__name__)


def get_requirements(recipe, profile, log):
    name, _ = recipe.ref.split('/')

    options_cmd = []
    if recipe.options:
        for opt in recipe.options:
            options_cmd.extend(['-o', opt])

    output_file = os.path.join('.graphlock', recipe.ref.replace('/', '-') + '.lock')
    cmd = ['graph', 'lock', '--build', '--profile', profile, '--lockfile', output_file] + options_cmd + [recipe.ref + '@']
    r = run_conan(cmd)

    if 'Invalid configuration' in r:
        log.warn(r)
        return None, None

    try:
        content = json.loads(tools.load(output_file))
        for _, node in content['graph_lock']['nodes'].items():
            ref, _ = node['pref'].split('#')
            if ref == recipe.ref:
                reqs = [k.split('#', 1)[0] for k, _ in node.get('requires', {}).items()]
                return reqs, []
        
        assert False, "Never get here!"
    except Exception as e:
        log.error("Error!!! {}".format(e))
        log.error(" - recipe: ".format(recipe))
        log.error(" - profile: ".format(profile))
        log.error(r)
    return None, None

