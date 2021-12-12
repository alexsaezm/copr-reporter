import json
import configparser
from copr.v3 import Client
from munch import Munch


def load_config(file):
    c = configparser.ConfigParser()
    c.read(file)
    return c


def retrieve_packages(project_owner, project_name):
    c = Client.create_from_config_file()
    p = c.package_proxy.get_list(project_owner, project_name, pagination={"order": "name"}, with_latest_build=True)
    return p


def retrieve_builds(package):
    c = Client.create_from_config_file()
    b = c.build_chroot_proxy.get_list(package.builds['latest']['id'])
    return b


if __name__ == '__main__':
    config = load_config(file="./config.ini")
    packages_a = retrieve_packages(config['current']['owner'], config['current']['project'])
    packages_b = retrieve_packages(config['next']['owner'], config['next']['project'])

    packages = {}
    for pa, pb in zip(packages_a, packages_b):
        new_package = Munch(name=pa.name)
        new_package.builds_a = {}
        new_package.builds_b = {}
        builds_a = retrieve_builds(pa)
        builds_b = retrieve_builds(pb)
        for ba, bb in zip(builds_a, builds_b):
            # Stores the arch, the URL and the state of the build using the the chroot as a key
            arch = ba.name.split('-')[-1]
            new_package.builds_a[ba.name] = Munch(arch=arch, url=ba.result_url, state=ba.state)
            arch = ba.name.split('-')[-1]
            new_package.builds_b[bb.name] = Munch(arch=arch, url=bb.result_url, state=bb.state)
        packages[pa.name] = new_package

    with open("packages.json", "w") as out:
        json.dump(packages, out, indent=2)
