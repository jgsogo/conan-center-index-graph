import logging
from dataclasses import dataclass
from typing import Optional

from conans.model.ref import ConanFileReference

log = logging.getLogger(__name__)


@dataclass
class Recipe:
    ref: ConanFileReference
    conanfile: str
    options: Optional[tuple] = None
    is_draft: bool = False
    is_proxy: bool = False

    @property
    def ref_str(self):
        return f"{self.ref.name}-{self.ref.version}"
