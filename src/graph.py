import argparse
import itertools
import logging
import os
import shutil
from typing import Tuple

from conans import tools

from cci.graph import Graph
from cci.recipe import Recipe
from cci.recipes import explode_options_without_duplicates
from cci.recipes import get_recipe_list
from cci.repository import Repository
from cci.run_conan import ConanWrapper
from cci.settings import get_profiles
from cci.types import PATH

conan_center_index = Repository(url='https://github.com/conan-io/conan-center-index.git', branch='master')


me = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger('cci')


def configure_log():
    log.setLevel(logging.WARNING)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)


def main(conan: ConanWrapper, working_dir: PATH, args: argparse.Namespace):
    # Get recipes
    draft_folder = os.path.join(me, '..', 'recipe_drafts') if args.add_drafts else None
    recipes = list(get_recipe_list(cci_repo=conan_center_index, cwd=working_dir, draft_folder=draft_folder))
    log.info(f"Found {len(recipes)} recipes")

    # Get profiles
    profiles_dir = os.path.abspath(os.path.join(me, '..', 'conf', 'profiles'))
    profiles = list(get_profiles(profiles_dir))  # TODO: Add filter using input cmd argument
    log.info(f"Found {len(profiles)} profiles")

    # Start to work with Conan itself
    all_jobs = []
    for recipe in recipes:
        conan.export(recipe)
        all_jobs.append([recipe] if not args.explode_options else explode_options_without_duplicates(recipe))

    all_jobs = itertools.product(profiles, itertools.chain.from_iterable(all_jobs))

    def _per_job(profile_recipe: Tuple[PATH, Recipe]) -> Tuple[PATH, Recipe, list, list, list]:
        profile_, recipe_ = profile_recipe
        log_line = f"Recipe: '{recipe_.ref}' | Profile: '{os.path.basename(profile_)}'"
        if args.explode_options:
            log_line += f" | Options: '{recipe_.options}'"
        log.info(log_line)
        reqs, breqs, pyreqs = conan.requirements(recipe_, profile_)
        return profile_, recipe_, reqs, breqs, pyreqs

    """
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool(args.threads)
    results = pool.map(_per_job, all_jobs)
    pool.close()
    pool.join()
    """

    graph = Graph()

    results = map(_per_job, all_jobs)
    for profile, recipe, reqs, breqs, pyreqs in results:
        graph.add_node(recipe.ref, profile, is_draft=recipe.is_draft)
        for it in (reqs or []) + (breqs or []) + (pyreqs or []):
            graph.add_edge(recipe.ref, it, profile, is_draft=recipe.is_draft)

    graphviz_file = os.path.join(working_dir, 'graphviz.dot')
    log.info(f"Draw the graph in '{graphviz_file}'")
    graphviz = graph.export_graphviz(include_drafts=False)
    tools.save(graphviz_file, graphviz.source)
    cmps = graph.compute_max_connected_component(include_drafts=False)

    graphviz_w_drafts_file = os.path.join(working_dir, 'graphviz-drafts.dot')
    log.info(f"Draw the graph (with drafts) in '{graphviz_w_drafts_file}'")
    graphviz = graph.export_graphviz(include_drafts=True)
    tools.save(graphviz_w_drafts_file, graphviz.source)
    cmps_drafts = graph.compute_max_connected_component(include_drafts=True)

    print("Some stats:")
    print(" - recipes: {}".format(len([it for it in graph.nodes.values() if not it.is_draft])))
    print(" - requires relations: {}".format(len([it for it in graph.edges.values() if not it.is_draft])))
    print(" - recipes x versions: {}".format(sum([len(n.versions) for n in graph.nodes.values() if not n.is_draft])))
    print(" - components: {}".format(len(cmps)))
    print(" - components-max: {}".format(max([len(it) for it in cmps])))
    if args.add_drafts:
        print("Added drafts:")
        print(" - drafts: {}".format(len([it for it in graph.nodes.values() if it.is_draft])))
        print(" - requires relations (drafts): {}".format(len([it for it in graph.edges.values() if it.is_draft])))
        print(" - components (drafts): {}".format(len(cmps_drafts)))
        print(" - components-max (drafts): {}".format(max([len(it) for it in cmps_drafts])))


if __name__ == '__main__':
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

    configure_log()
    conan = ConanWrapper(cwd=working_dir, conan_user_home=working_dir)

    main(conan, working_dir, args)
