import subprocess
import logging
from conans.util.files import mkdir, get_abs_path, walk, decode_text
from collections import namedtuple
import argparse
from conans.client.tools import chdir
from cci_recipe_list import get_recipe_list
from settings import get_profiles
import os
from run_conan import run_conan
from utils import run, context_env
from itertools import product
import shutil
from recipe_options import explode_options, explode_options_without_duplicates
from recipe_requirements import get_requirements
from graphviz import Digraph


log = logging.getLogger(__name__)
me = os.path.abspath(os.path.dirname(__file__))

Repo = namedtuple("Repo", ["url", "branch"])
conan_center_index = Repo('https://github.com/conan-io/conan-center-index.git', 'master')


def clone(repo):
    log.info("Clone repo '{}'".format(repo.url))
    cmd = ['git', 'clone', '--depth', '1', repo.url]
    if repo.branch:
        cmd.extend(['-b', repo.branch])
    run(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create conan-center-index map')
    parser.add_argument('--working-dir', type=str, help='working directory')
    parser.add_argument('--explode-options', action='store_true', help='Explode options (use wise algorithm)')
    args = parser.parse_args()

    working_dir = os.path.abspath(args.working_dir)

    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    with chdir(working_dir):
        # clone(conan_center_index)

        # Get recipes
        recipes = list(get_recipe_list('conan-center-index'))
        log.info("Found {} recipes".format(len(recipes)))

        # Get profiles
        settings = os.path.abspath(os.path.join(me, '..', 'conf', 'settings.yml'))
        profiles = list(get_profiles(settings))  # TODO: Add filter using input cmd argument
        log.info("Computed {} profiles".format(len(profiles)))

        # Explode options (optional)
        # TODO: Add input argument to make this optional
        recipes_with_options = []
        if args.explode_options:
            for recipe in recipes:
                log.debug("Explode options for recipe: '{}'".format(recipe.ref))
                recipes_with_options += list(explode_options_without_duplicates(recipe))
            log.info("Found {} recipes after exploding options".format(len(recipes_with_options)))
        else:
            recipes_with_options = recipes

        # Start to work with Conan itself
        with context_env(CONAN_USER_HOME=working_dir):
            dot = Digraph(comment='Conan Center')

            # Export all recipes
            for recipe in recipes:
                ori, _ = recipe.ref.split('/')
                dot.node(ori)
                r = run_conan(["export", recipe.conanfile, recipe.ref + '@'])
            
            # Get the requirements for all the recipe/profile/options
            total = len(profiles)*len(recipes_with_options)
            for i, (profile, recipe) in enumerate(product(profiles, recipes_with_options)):
                log_line = "Recipe: '{}' | Profile: '{}'".format(recipe.ref, profile)
                if args.explode_options:
                    log_line += " | Options: '{}'".format(recipe.options)
                log.info("[{}/{}] {}".format(i, total, log_line))
                reqs = get_requirements(recipe, profile)
                if not reqs:
                    continue
                log.info(" - reqs: {}".format(reqs))
                    
                ori, _ = recipe.ref.split('/')
                for it in reqs:
                    dst, _ = it.split('/')
                    dot.edge(ori, dst)

            graphviz = os.path.join(working_dir, 'graphviz')
            log.info("Draw the graph in '{}'".format(graphviz))
            tools.save(graphviz, dot.source)

