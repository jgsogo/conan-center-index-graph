import itertools
from collections import Iterable


def flatten(coll):
    for i in coll:
        if isinstance(i, Iterable) and not isinstance(i, str):
            for subc in flatten(i):
                yield subc
        else:
            yield i


def get_profile_list(keys, profiles_generator):
    ret = []
    for pr in list(profiles_generator):
        pr = [v if not isinstance(v, str) else (v, ) for v in pr]
        for pr in itertools.product(*pr):
            pr = flatten(pr)
            ret.append({k: v for k, v in zip(keys, pr)})
    return ret


def get_linux_profiles(use_cppstd):
    # - Linux
    linux_keys = ('os', 'arch', 'compiler', 'compiler.version', 'compiler.libcxx', 'build_type')
    linux_cppstd = ('98', '11', '14', '17', '20')
    linux_profiles_generator = (
        ('Linux',), 
        #('x86', 'x86_64'), 
        ('x86_64',), 
        (
            list(itertools.product(('gcc',), ("4.9", "5", "6", "7", "8", "9"), ('libstdc++', 'libstdc++11'))), 
            list(itertools.product(('clang',), ("3.9", "4.0", "5.0", "6.0", "7.0", "8", "9"), ('libc++', 'libstdc++')))
        ),
        ('Debug', 'Release')
    )

    if use_cppstd:
        linux_keys = linux_keys + ('compiler.cppstd', )
        linux_profiles_generator = linux_profiles_generator + (linux_cppstd, )

    prs = get_profile_list(linux_keys, itertools.product(*linux_profiles_generator))
    for it in prs:
        if it['compiler'] == 'gcc' and it['compiler.version'] == '4.9' and it['compiler.libcxx'] == 'libstdc++11':
            continue
        yield it

def get_windows_profiles(use_cppstd):
    windows_keys = ('os', 'arch', 'compiler', 'compiler.version', 'compiler.runtime', 'build_type')
    windows_cppstd = ('11', '14', '17', '20')
    windows_profiles_generator = (
        ('Windows',), 
        #('x86', 'x86_64'), 
        ('x86_64',), 
        (
            list(itertools.product(('Visual Studio',), ("14", "15", "16"), ('MT', 'MD'))), 
        ),
        ('Debug', 'Release')
    )

    if use_cppstd:
        windows_keys = windows_keys + ('compiler.cppstd', )
        windows_profiles_generator = windows_profiles_generator + (windows_cppstd, )

    prs = get_profile_list(windows_keys, itertools.product(*windows_profiles_generator))
    for it in prs:
        if it['build_type'] == 'Debug':
            it['compiler.runtime'] = it['compiler.runtime'] + 'd'
        yield it
    
def get_macos_profiles(use_cppstd):
    macos_keys = ('os', 'arch', 'compiler', 'compiler.version', 'compiler.libcxx', 'build_type')
    macos_cppstd = ('98', '11', '14', '17', '20')
    macos_profiles_generator = (
        ('Macos',), 
        #('x86', 'x86_64'), 
        ('x86_64',), 
        (
            list(itertools.product(('apple-clang',), ("9.1", "10.0", "11.0"), ('libc++', ))), 
        ),
        ('Debug', 'Release')
    )

    if use_cppstd:
        macos_keys = macos_keys + ('compiler.cppstd', )
        macos_profiles_generator = macos_profiles_generator + (macos_cppstd, )

    prs = get_profile_list(macos_keys, itertools.product(*macos_profiles_generator))
    for it in prs:
        yield it
    
