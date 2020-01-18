import contextlib
import logging
import os
import re
import subprocess
import tempfile
from typing import List, Optional

from conans.util.files import decode_text

from cci import types

log = logging.getLogger(__name__)


def run(command: List[str], working_dir: Optional[types.PATH] = None) -> str:
    log.debug(f"Run command: {' '.join(command)}")
    out, _ = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=working_dir).communicate()
    out = decode_text(out)
    log.debug(out)
    return out


@contextlib.contextmanager
def temp_file(filename: str = 'tmpfile') -> types.PATH:
    with temp_folder() as tf:
        tmpfile = os.path.join(tf, filename)
        try:
            yield tmpfile
        finally:
            os.unlink(tmpfile)


@contextlib.contextmanager
def temp_folder() -> types.PATH:
    td = tempfile.mkdtemp()
    try:
        yield td
    finally:
        os.rmdir(td)


@contextlib.contextmanager
def _context_restore():
    old_environ = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


@contextlib.contextmanager
def clean_context_env(pattern):
    expr = re.compile(pattern)
    with _context_restore():
        for key, val in dict(os.environ).items():
            if expr.match(key):
                del os.environ[key]
        yield


@contextlib.contextmanager
def context_env(**environ):
    with _context_restore():
        os.environ.update(environ)
        yield
