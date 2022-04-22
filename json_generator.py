import json
import configparser
from copr.v3 import Client
from munch import Munch


def load_config(file):
    c = configparser.ConfigParser()
    c.read(file)
    return c

def create_missing_package(name):
    return Munch(name = name, state = 'missing', builds = {'latest' : None })

def create_missing_build(arch):
    return Munch(name = arch, state = 'missing', result_url = '')

def retrieve_packages(client, project_owner, project_name):
    c = Client.create_from_config_file()
    p = client.package_proxy.get_list(project_owner, project_name, pagination={"order": "name"}, with_latest_build=True)
    return p

def handle_missing_packages(packages_a, packages_b):

    n = 0
    while n < max(len(packages_a), len(packages_b)):
        pa = packages_a[n]
        pb = packages_b[n]

        if pa.name < pb.name:
            packages_b.insert(n, create_missing_package(pa.name))
        elif pa.name > pb.name:
            packages_a.insert(n, create_missing_package(pb.name))
        n+=1

def get_chroot_arch(chroot):
    return chroot.split('-')[-1]

def has_arch(builds, arch):
    for build in builds:
        if get_chroot_arch(build.name) == arch:
            return True
    return False

def handle_missing_builds(builds_a, builds_b):
    arches = set([])
    for builds in [builds_a, builds_b]:
        for build in builds:
            arch = build.name.split('-')[-1]
            if arch not in arches:
                arches.add(arch)

    for arch in arches:
        for builds in [builds_a, builds_b]:
            if not has_arch(builds, arch):
                builds.append(create_missing_build(arch))

def retrieve_builds(client, package):

    latest_build = package.builds['latest']
    if not latest_build:
        return []

    # When a build has state of succeeded, we don't need to query COPR for
    # more information, because we know the builds have succeeded for all
    # chroots.  A 'failed' state means that there was at least 1 failure,
    # so in that case we still need to query COPR to see which chroots
    # suceeded and which chroots failed.
    if latest_build['state'] == 'succeeded':
        builds = []
        for c in sorted(latest_build['chroots']):
            builds.append(Munch(name=c, result_url='{}/{}/0{}-{}/'.format(latest_build['repo_url'], c, latest_build['id'], package.name),
                                           state = latest_build['state']))
        return builds


    b = client.build_chroot_proxy.get_list(package.builds['latest']['id'])
    return b


if __name__ == '__main__':
    config = load_config(file="./config.ini")
    client_a = Client.create_from_config_file(config.get('current', 'config', fallback = None))
    client_b = Client.create_from_config_file(config.get('next', 'config', fallback = None))
    packages_a = retrieve_packages(client_a, config['current']['owner'], config['current']['project'])
    packages_b = retrieve_packages(client_b, config['next']['owner'], config['next']['project'])
    handle_missing_packages(packages_a, packages_b)

    packages = {}
    for pa, pb in zip(packages_a, packages_b):
        new_package = Munch(name=pa.name)
        new_package.builds_a = {}
        new_package.builds_b = {}
        builds_a = retrieve_builds(client_a, pa)
        builds_b = retrieve_builds(client_b, pb)
        handle_missing_builds(builds_a, builds_b)
        sort_key = lambda x : get_chroot_arch(x.name)
        for ba, bb in zip(sorted(builds_a, key = sort_key), sorted(builds_b, key = sort_key)):
            # Stores the arch, the URL and the state of the build using the the chroot as a key
            arch = ba.name.split('-')[-1]
            new_package.builds_a[ba.name] = Munch(arch=arch, url=ba.result_url, state=ba.state)
            arch = ba.name.split('-')[-1]
            new_package.builds_b[bb.name] = Munch(arch=arch, url=bb.result_url, state=bb.state)
        packages[pa.name] = new_package

    with open("packages.json", "w") as out:
        json.dump(packages, out, indent=2)
