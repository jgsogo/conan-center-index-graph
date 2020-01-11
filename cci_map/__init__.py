import subprocess
import logging
from conans.util.files import mkdir, get_abs_path, walk, decode_text
from collections import namedtuple
log = logging.getLogger(__name__)

Repo = namedtuple("Repo", ["url", "branch"])
conan_center_index = Repo('https://github.com/conan-io/conan-center-index.git', 'master')

def run(command):
    log.debug("Run command: '{}'".format(" ".join(command)))
    out, _ = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()
    out = decode_text(out)
    log.debug(out)
    return out

def clone(repo):
    log.info("Clone repo '{}'".format(repo.url))
    cmd = ['git', 'clone', '--depth', '1', repo.url]
    if repo.branch:
        cmd.extend(['-b', repo.branch])
    run(cmd)

if __name__ == "__main__":
    clone(conan_center_index)
