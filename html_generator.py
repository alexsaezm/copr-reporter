import json
import datetime

import jinja2


# TODO: Add a summary of the new broken packages
# TODO: Add in the summary the total amount of packages
def generate_report(title, results):
    loader = jinja2.FileSystemLoader(searchpath="./")
    environment = jinja2.Environment(loader=loader)
    file = "template.html"

    template = environment.get_template(file)
    text = template.render(
        title=title,
        date=datetime.datetime.now().isoformat(),
        results=results
    )
    report = open("report.html", 'w')
    report.write(text)
    report.close()


if __name__ == '__main__':
    title = "Go updates dashboard"
    description = """This page contains the results of the builds made in this two COPR repositores:
    - https://copr.fedorainfracloud.org/coprs/alexsaezm/go-current-packages
    - https://copr.fedorainfracloud.org/coprs/alexsaezm/go-next-packages
    
    Explanation of the columns:
    Name: The name of the package.
    Builds with current Go release: Rebuild Fedora 35 Go dependant packages using Fedora 35 current Go package.
    Builds with next Go release: Rebuild Fedora 35 Go dependant packages using Fedora Rawhide current Go package.
    Changes: Notes so you can search results easily.
    """
    packages = {}
    with open("packages.json", "r") as f:
        packages = json.load(f)

    for k, v in packages.items():
        packages[k]['changed'] = 'Same results'
        for a, b in zip(v['builds_a'], v['builds_b']):
            state_a = packages[k]['builds_a'][a]['state']
            state_b = packages[k]['builds_b'][b]['state']
            if state_a != state_b:
                packages[k]['changed'] = "Something has changed. You should verify the builds"
    generate_report(title, packages)
