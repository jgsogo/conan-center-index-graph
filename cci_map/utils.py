import logging
import subprocess
from conans.util.files import mkdir, get_abs_path, walk, decode_text

log = logging.getLogger(__name__)

def run(command):
    log.debug("Run command: '{}'".format(" ".join(command)))
    out, _ = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()
    out = decode_text(out)
    log.debug(out)
    return out

import contextlib
import os
import re


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
