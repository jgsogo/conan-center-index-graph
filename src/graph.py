
import logging
import argparse
import os
import shutil
import itertools
from cci.recipes import get_recipe_list
from cci.repository import Repository
from cci.utils import context_env
from cci.settings import get_profiles
from cci.graph import Graph
from cci.run_conan import initialize_conan, ConanWrapper
from cci.recipe import explode_options_without_duplicates
from cci.types import PATH
from typing import Tuple
from cci.recipe import Recipe
import argparse
import logging
import os
import shutil
from itertools import product
from multiprocessing.dummy import Pool as ThreadPool

from conans import tools

conan_center_index = Repository(url='https://github.com/conan-io/conan-center-index.git', branch='master')


me = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger('cci')


def configure_log():
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)


def main(working_dir, args):
    # Get recipes
    draft_folder = os.path.join(me, '..', 'recipe_drafts') if args.add_drafts else None
    recipes = list(get_recipe_list(cci_repo=conan_center_index, cwd=working_dir, draft_folder=draft_folder))
    log.info(f"Found {len(recipes)} recipes")

    # Get profiles
    profiles_dir = os.path.abspath(os.path.join(me, '..', 'conf', 'profiles'))
    profiles = list(get_profiles(profiles_dir))  # TODO: Add filter using input cmd argument
    log.info(f"Found {len(profiles)} profiles")

    # Start to work with Conan itself
    with context_env(CONAN_USER_HOME=working_dir):
        all_jobs = []
        for recipe in recipes:
            recipe.export()
            all_jobs.append([recipe] if not args.explode_options else explode_options_without_duplicates(recipe))

        all_jobs = itertools.product(profiles, itertools.chain.from_iterable(all_jobs))

        def _per_job(profile_recipe: Tuple[PATH, Recipe]):
            profile_, recipe_ = profile_recipe
            log_line = f"Recipe: '{recipe_.ref}' | Profile: '{os.path.basename(profile_)}'"
            if args.explode_options:
                log_line += f" | Options: '{recipe_.options}'"
            log.info(log_line)
            reqs, breqs = recipe_.requirements(profile_, log)
            return profile_, recipe_, reqs, breqs

        pool = ThreadPool(args.threads)
        results = pool.map(_per_job, all_jobs)
        pool.close()
        pool.join()

    graph = Graph()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create conan-center-index map')
    #parser.add_argument('--working-dir', type=str, help='working directory')
    parser.add_argument('--threads', type=int, default=32, help='working directory')
    parser.add_argument('--explode-options', action='store_true', help='Explode options (use wise algorithm)')
    parser.add_argument('--add-drafts', action='store_true', help='Add recipe drafts')
    args = parser.parse_args()

    configure_log()

    working_dir = os.path.abspath(os.path.join(me, '..', '_working_dir'))
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.mkdir(working_dir)

    initialize_conan(cwd=working_dir)

    main(working_dir, args)