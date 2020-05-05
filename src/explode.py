import argparse
import itertools
import logging
import os
import shutil
import json
from typing import Tuple
from collections import defaultdict

from conans import tools

from cci.graph import Graph
from cci.recipe import Recipe
from cci.recipes import explode_shared_option
from cci.recipes import get_recipe_list
from cci.repository import Repository
from cci.run_conan import ConanWrapper
from cci.settings import get_profiles
from cci.types import PATH
from cci.profiles import get_linux_profiles, get_windows_profiles, get_macos_profiles
from cci.utils import temp_file

conan_center_index = Repository(url='https://github.com/conan-io/conan-center-index.git', branch='master')


me = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger('cci')


def configure_log():
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    log.addHandler(ch)


def main(conan: ConanWrapper, working_dir: PATH, args: argparse.Namespace):
    use_cppstd = args.use_cppstd
    # Get recipes
    recipes = list(get_recipe_list(cci_repo=conan_center_index, cwd=working_dir, draft_folder=None))
    log.info(f"Found {len(recipes)} recipes")

    # Get settings profiles
    linux_profiles = list(get_linux_profiles(use_cppstd))
    windows_profiles = list(get_windows_profiles(use_cppstd))
    macos_profiles = list(get_macos_profiles(use_cppstd))

    log.info(f"Computed {len(linux_profiles)} profiles for Linux")
    log.info(f"Computed {len(windows_profiles)} profiles for Windows")
    log.info(f"Computed {len(macos_profiles)} profiles for Macos")

    # Write down profiles
    profiles = []
    os.mkdir(os.path.join(working_dir, 'profiles'))
    for i, profile in enumerate(linux_profiles + windows_profiles + macos_profiles):
        path = os.path.join(working_dir, 'profiles', f'profile_{i}')
        with open(path, 'w') as f:
            f.write("[settings]\n")
            for k, v in profile.items():
                f.write(f"{k}={v}\n")
        profiles.append(path)

    # Export all recipes
    for recipe in recipes:
        conan.export(recipe)

    # Start to work with Conan itself
    all_jobs = []
    for recipe in recipes:
        all_jobs.append(explode_shared_option(recipe, conan))

    all_jobs = itertools.product(profiles, itertools.chain.from_iterable(all_jobs))

    def _per_job(profile_recipe: Tuple[PATH, Recipe]) -> Tuple[PATH, Recipe, list, list, list]:
        profile_, recipe_ = profile_recipe
        log_line = f"Recipe: '{recipe_.ref}' | Profile: '{profile_}' | Options: '{recipe_.options}'"
        log.info(log_line)
        
        ok, pid = conan.package_id(recipe_, profile_)
        return recipe_, profile_, ok, pid
        
    # Compute parallel
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool(args.threads)
    results = pool.map(_per_job, all_jobs)
    pool.close()
    pool.join()
    
    # Compute
    #results = map(_per_job, all_jobs)

    # Store output
    output = defaultdict(list)
    for recipe, profile, ok, pid in results:
        output[str(recipe.ref)].append((profile, pid))
    
    output_results = os.path.join(working_dir, f'data{".cppstd" if use_cppstd else ""}.json')
    print(f"Output: {output_results}")
    with open(output_results, 'w') as f:
        f.write(json.dumps(output))

    # Some stats
    total = 0
    for ref, pids in output.items():
        uniques = set([it[1] for it in pids])
        uniques = [it for it in uniques if it is not None]
        total += len(uniques)
        print(f"{ref}: {len(uniques)}")

    print(f"Total binaries: {total}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute binary explosion')
    #parser.add_argument('--working-dir', type=str, help='working directory')
    parser.add_argument('--threads', type=int, default=32, help='threads')
    #parser.add_argument('--explode-options', action='store_true', help='Explode options (use wise algorithm)')
    parser.add_argument('--use-cppstd', action='store_true', help='Add CPPSTD combinations')
    args = parser.parse_args()

    working_dir = os.path.abspath(os.path.join(me, '..', '_working_dir'))
    if os.path.exists(working_dir):
        shutil.rmtree(working_dir)
    os.mkdir(working_dir)

    configure_log()
    conan = ConanWrapper(cwd=working_dir, conan_user_home=working_dir)

    main(conan, working_dir, args)
