import logging
import sys
from io import StringIO
from typing import List, Optional

from conans.client.command import Command, Conan
from conans.client.tools import chdir

from cci import types

log = logging.getLogger(__name__)


class ConanWrapper:
    cwd: types.PATH = None
    stream = StringIO()
    _instance = None

    def __new__(cls, cwd=None):
        # Check if an instance exists:
        if not cls._instance:
            assert cwd, "First instance requires a working directory"
            # Create new instance:
            cls._instance = object.__new__(cls)

            # We need to impostate stdout/err during creation
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = cls.stream, cls.stream
            conan_api, cache, user_io = Conan.factory()
            cls._instance.cmd = Command(conan_api)
            sys.stdout, sys.stderr = old_stdout, old_stderr
            cls._instance.cwd = cwd
        return cls._instance

    def run(self, command: List[str], cwd: Optional[types.PATH] = None):
        self.stream.truncate(0)
        try:
            with chdir(cwd or self.cwd):
                return_code = self.cmd.run(command)
        except Exception as e:
            # Conan execution failed
            log.error("Command failed: {}".format(e))
        return self.stream.getvalue()


def initialize_conan(cwd):
    conan = ConanWrapper(cwd=cwd)
    return conan
