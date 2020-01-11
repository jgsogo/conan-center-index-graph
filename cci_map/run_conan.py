
from contextlib import contextmanager

import sys
from conans import __version__ as conan_version
from conans.client.command import Conan, CommandOutputer, Command
from conans.model.version import Version
import os
import shutil
import tempfile
import unittest
import uuid

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


@contextmanager
def conan_command(output_stream):
    # This snippet reproduces code from conans.client.command.main, we cannot directly
    # use it because in case of error it is exiting the python interpreter :/
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = output_stream, output_stream
    conan_api, cache, user_io = Conan.factory()
    if Version(conan_version) >= "1.16":
        cmd = Command(conan_api)
    else:
        user_io.out._stream = output_stream
        outputer = CommandOutputer(user_io, cache)
        cmd = Command(conan_api, cache, user_io, outputer)
    try:
        yield cmd
    finally:
        if Version(conan_version) < "1.13":
            conan_api._remote_manager._auth_manager._localdb.connection.close()  # Close sqlite3
        sys.stdout, sys.stderr = old_stdout, old_stderr


def run_conan(command):
    stream = StringIO()
    with conan_command(stream) as cmd:
        try:
            return_code = cmd.run(command)
        except Exception as e:
            # Conan execution failed
            log.error("Command failed: {}".format(e))
    return stream.getvalue()
