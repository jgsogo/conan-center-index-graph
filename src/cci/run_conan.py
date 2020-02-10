import json
import logging
import os
from io import StringIO
from typing import List, Optional

from conans import tools
from conans.client.command import Command
from conans.client.conan_api import ConanAPIV1, ConanOutput
from conans.client.tools import chdir
from conans.model.ref import ConanFileReference

from cci import types
from cci.utils import temp_file

log = logging.getLogger(__name__)


class ConanWrapper:
    _cwd: types.PATH
    _conan_user_home: types.PATH

    def __init__(self, conan_user_home: types.PATH, cwd: types.PATH):
        self._cwd = cwd
        self.stream = StringIO()
        output = ConanOutput(self.stream, self.stream, color=False)
        conan_api = ConanAPIV1(cache_folder=conan_user_home, output=output)
        self.cmd = Command(conan_api)

    def run(self, command: List[str], cwd: Optional[types.PATH] = None):
        log.debug(f"Run command '{' '.join(command)}'")
        self.stream.truncate(0)
        try:
            with chdir(cwd or self._cwd):
                r = self.cmd.run(command)
        except Exception as e:
            # Conan execution failed
            log.error(f"Command unexpectedly failed: {e}")
            return -1, str(e)
        else:
            return r, self.stream.getvalue()

    def inspect(self, recipe, attributes):
        # Return options attribute and default_options as dictionary
        with temp_file() as json_file:
            cmd = ['inspect']
            for it in attributes:
                cmd.extend(['-a', it])
            cmd.extend(['--json', json_file, recipe.conanfile])
            self.run(cmd)
            data = json.loads(tools.load(json_file))
        return tuple([data[it] for it in attributes])

    def export(self, recipe):
        log.info(f"Export recipe {recipe.ref}")
        self.run(command=["export", recipe.conanfile, f"{recipe.ref}@"])

    @staticmethod
    def get_reference(nodes, node_id):
        node = nodes[node_id]
        reference, _ = node['pref'].split('#')
        ref = ConanFileReference.loads(reference)
        return ref

    def requirements(self, recipe, profile):
        options_cmd = []
        if recipe.options:
            for opt in recipe.options:
                options_cmd.extend(['-o', opt])

        with temp_file('conan.lock') as output_file:
            cmd = ['graph', 'lock', '--build', '--profile', profile, '--lockfile', output_file] \
                  + options_cmd + [f"{recipe.ref}@"]

            try:
                r, out = self.run(cmd)
                if 'Invalid configuration' in out:
                    return None, None, None
                elif r != 0:
                    log.warning(f"Error in recipe {recipe.ref}: {out}")
                    return None, None, None

                content = json.loads(tools.load(output_file))
                nodes = content['graph_lock']['nodes']
                for _, node in nodes.items():
                    reference, _ = node['pref'].split('#')
                    ref = ConanFileReference.loads(reference)
                    if ref == recipe.ref:
                        reqs = [self.get_reference(nodes, it) for it in node.get('requires', [])]
                        breqs = [self.get_reference(nodes, it) for it in node.get('build_requires', [])]
                        pyreqs = [self.get_reference(nodes, it) for it in node.get('python_requires', [])]
                        return reqs, breqs, pyreqs

                assert False, "Never get here!"
            except Exception as e:
                log.error(f"Error in recipe {recipe.ref}!!! {e}")
                log.error(f" - recipe: {recipe.ref}")
                log.error(f" - profile: {os.path.basename(profile)}")
                log.error(r)
        return None, None, None
