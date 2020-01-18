import contextlib
import logging
import os
import re
import subprocess

from conans.util.files import decode_text, get_abs_path, mkdir, walk

log = logging.getLogger(__name__)


def run(command, working_dir=None):
    log.debug("Run command: '{}'".format(" ".join(command)))
    out, _ = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=working_dir).communicate()
    out = decode_text(out)
    log.debug(out)
    return out



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
