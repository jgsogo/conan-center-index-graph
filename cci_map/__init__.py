import subprocess
import logging
from conans.util.files import mkdir, get_abs_path, walk, decode_text
from collections import namedtuple
import argparse
from conans.client.tools import chdir
from cci_recipe_list import get_recipe_list, get_recipe_drafts
from settings import get_profiles
import os
from run_conan import run_conan
from utils import run, context_env
from multiprocessing.dummy import Pool as ThreadPool
from itertools import product
import shutil
from recipe_options import explode_options, explode_options_without_duplicates
from recipe_requirements import get_requirements
from conans import tools
from graph import Graph


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
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create conan-center-index map')
    #parser.add_argument('--working-dir', type=str, help='working directory')
    parser.add_argument('--threads', type=int, default=32, help='working directory')
    parser.add_argument('--explode-options', action='store_true', help='Explode options (use wise algorithm)')
    parser.add_argument('--add-drafts', action='store_true', help='Add recipe drafts')
    args = parser.parse_args()

    working_dir = os.path.abspath(os.path.join(me, '..', '_working_dir'))
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.mkdir(working_dir)

    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)

    with chdir(working_dir):
        # Clone Conan Center Index
        clone(conan_center_index)

        # Get recipes
        recipes = list(get_recipe_list('conan-center-index'))
        log.info("Found {} recipes".format(len(recipes)))

        # Get profiles
        profiles_dir = os.path.abspath(os.path.join(me, '..', 'conf', 'profiles'))
        profiles = list(get_profiles(profiles_dir))  # TODO: Add filter using input cmd argument
        log.info("Found {} profiles".format(len(profiles)))

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
            graph = Graph()

            results = do_work(recipes, recipes_with_options, profiles, graph, args.threads, explode_options=args.explode_options, is_draft=False)

            # Iterate drafts
            results_drafts = []
            if args.add_drafts:
                drafts = list(get_recipe_drafts(os.path.join(me, '..', 'recipe_drafts')))
                actual_recipe_names = graph.nodes.keys()
                drafts = [d for d in drafts if d.ref.split('/')[0] not in actual_recipe_names]  # TODO: Log removed recipes
                log.info("Found {} recipe drafts".format(len(drafts)))

                draft_profile = os.path.join(profiles_dir, 'draft')
                results_drafts = do_work(drafts, drafts, [draft_profile], graph, args.threads, explode_options=False, is_draft=True)

    for profile, recipe, reqs, breqs in results:
        graph.add_node(recipe.ref, profile)
        for it in reqs or []:
            graph.add_edge(recipe.ref, it, profile)
        for it in breqs or []:
            graph.add_edge(recipe.ref, it, profile)

    print("Some stats:")
    print(" - recipes: {}".format(len(graph.nodes)))
    print(" - requires relations: {}".format(len(graph.edges)))
    print(" - recipes x versions: {}".format(sum([len(n.versions) for n in graph.nodes.values()])))

    for profile, recipe, reqs, breqs in results_drafts:
        graph.add_node(recipe.ref, profile, is_draft=True)
        for it in reqs or []:
            graph.add_edge(recipe.ref, it, profile, is_draft=True)
        for it in breqs or []:
            graph.add_edge(recipe.ref, it, profile, is_draft=True)

    graphviz_file = os.path.join(working_dir, 'graphviz.dot')
    log.info("Draw the graph in '{}'".format(graphviz_file))
    graphviz = graph.export_graphviz()
    tools.save(graphviz_file, graphviz.source)

    print("Some stats (with drafts):")
    print(" - recipes: {}".format(len(graph.nodes)))
    print(" - requires relations: {}".format(len(graph.edges)))
    print(" - recipes x versions: {}".format(sum([len(n.versions) for n in graph.nodes.values()])))
