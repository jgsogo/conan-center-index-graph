import os
from typing import Iterator

from cci.types import PATH


def get_profiles(profiles_dir: PATH) -> Iterator[PATH]:
    for it in os.listdir(profiles_dir):
        if it == 'draft':  # Ignore draft profile
            continue
        yield os.path.join(profiles_dir, it)
