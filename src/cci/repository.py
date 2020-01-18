import logging
import os
import shutil
from dataclasses import dataclass, field
from typing import Optional, Iterator

import yaml
from conans import tools
from conans.model.ref import ConanFileReference

from cci import types
from cci.recipe import Recipe
from cci.utils import run

log = logging.getLogger(__name__)


@dataclass
class Repository:
    url: str
    branch: Optional[str]
    folder: Optional[types.PATH] = None
    _cloned_folder: field(init=False, repr=False) = None

    def __del__(self):
        if self._cloned_folder:
            shutil.rmtree(self._cloned_folder)

    @property
    def name(self):
        basename = os.path.basename(self.url)
        name, _ = os.path.splitext(basename)
        return name

    def clone(self, base_folder: types.PATH, name: Optional[str] = None) -> types.PATH:
        if not self._cloned_folder:
            log.info(f"Clone repo {self.url} in {base_folder}")
            cmd = ['git', 'clone', '--depth', '1', self.url]
            if self.branch:
                cmd.extend(['-b', self.branch])
            if name:
                cmd.extend([name])
            run(cmd, working_dir=base_folder)
            self._cloned_folder = os.path.join(base_folder, name or self.name)
        return self._cloned_folder

    def get_recipe_list(self) -> Iterator[Recipe]:
        log.info(f"Gather recipes from repo {self.name}")
        if not self._cloned_folder:
            raise RuntimeError("You need to close the repo first!")

        recipes_folder = os.path.abspath(os.path.join(self._cloned_folder, 'recipes'))
        for recipe in os.listdir(recipes_folder):
            config = os.path.join(recipes_folder, recipe, 'config.yml')
            if os.path.exists(config):
                data = yaml.safe_load(tools.load(config))
                for v, d in data["versions"].items():
                    ref = ConanFileReference(name=recipe, version=str(v), user=None, channel=None)
                    conanfile = os.path.join(recipes_folder, recipe, d["folder"], 'conanfile.py')
                    yield Recipe(ref=ref, conanfile=conanfile)
            else:
                for f in os.listdir(os.path.join(recipes_folder, recipe)):
                    ref = ConanFileReference(name=recipe, version=str(f), user=None, channel=None)
                    conanfile = os.path.join(recipes_folder, recipe, f, 'conanfile.py')
                    yield Recipe(ref=ref, conanfile=conanfile)
