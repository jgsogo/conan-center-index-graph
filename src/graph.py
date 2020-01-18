
import logging
import argparse
import os
import shutil

from cci.recipes import get_recipe_list
from cci.repository import Repository

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
    draft_folder = os.path.join(me, '..', 'recipe_drafts') if args.add_drafts else None
    recipes = get_recipe_list(cci_repo=conan_center_index, cwd=working_dir, draft_folder=draft_folder,
                              explode_options=args.explode_options)

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

    main(working_dir, args)