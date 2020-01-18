import logging
import os
from dataclasses import dataclass
from typing import Optional

from . import types
from .utils import run

log = logging.getLogger(__name__)


@dataclass
class Repository:
    url: str
    branch: Optional[str]
    folder: Optional[types.PATH] = None

    def name(self):
        basename = os.path.basename(self.url)
        name, _ = os.path.splitext(basename)
        return name

    def clone(self, base_folder: types.PATH, name: Optional[str] = None) -> types.PATH:
        log.info("Clone repo '{}'".format(self.url))
        cmd = ['git', 'clone', '--depth', '1', self.url]
        if self.branch:
            cmd.extend(['-b', self.branch])
        if name:
            cmd.extend([name])
        run(cmd, working_dir=base_folder)
        return os.path.join(base_folder, name or self.name())
