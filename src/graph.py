
import logging
import argparse
import os
import shutil

from cci.recipes import get_recipe_list
from cci.repository import Repository
from cci.utils import context_env
from cci.settings import get_profiles
from cci.graph import Graph
from cci.run_conan import initialize_conan

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

"""
def do_work(recipes, recipes_with_options, profiles, graph, threads, explode_options, is_draft):
    # Export all recipes
    for recipe in recipes:
        log.info(" - export recipe '{}'".format(recipe.ref))
        ori, _ = recipe.ref.split('/')
        r = run_conan(["export", recipe.conanfile, recipe.ref + '@'])
        graph.add_node(recipe.ref, is_draft=is_draft)

    # Get the requirements for all the recipe/profile/options
    jobs = list(product(profiles, recipes_with_options))
    total = len(jobs)

    def _per_job(profile_recipe):
        profile, recipe = profile_recipe
        log_line = "Recipe: '{}' | Profile: '{}'".format(recipe.ref, os.path.basename(profile))
        if explode_options:
            log_line += " | Options: '{}'".format(recipe.options)
        log.info(log_line)
        reqs, breqs = get_requirements(recipe, profile, log)
        return profile, recipe, reqs, breqs

    pool = ThreadPool(threads)
    results = pool.map(_per_job, jobs)
    pool.close()
    pool.join()
    return results
"""

def main(working_dir, args):
    # Get recipes
    draft_folder = os.path.join(me, '..', 'recipe_drafts') if args.add_drafts else None
    recipes = get_recipe_list(cci_repo=conan_center_index, cwd=working_dir, draft_folder=draft_folder,
                              explode_options=args.explode_options)

    # Get profiles
    profiles_dir = os.path.abspath(os.path.join(me, '..', 'conf', 'profiles'))
    profiles = list(get_profiles(profiles_dir))  # TODO: Add filter using input cmd argument
    log.info("Found {} profiles".format(len(profiles)))

    # Start to work with Conan itself
    with context_env(CONAN_USER_HOME=working_dir):
        graph = Graph()
        #results = do_work(recipes, recipes_with_options, profiles, graph, args.threads,
        #                  explode_options=args.explode_options, is_draft=False)


    for it in recipes:
        log.info(f" - recipe: {it}")
    exit()



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