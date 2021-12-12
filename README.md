# copr-reporter
Checks two COPR repositories and reports the amount of failures

This project was made for a Go SIG proposal. To follow upstream as close as we can.
The idea is that the last Fedora stable release (F35 but no F34 at this moment) can follow Go as close as we can so we don't need to make proposals with every fedora release
The Fedora N version is going to follow Go N until the Fedora N+1 is stable.
Example: Fedora 34 uses Go 1.16 as long as it can and Fedora 35 is going to follow upstream. When Fedora 36 is ready, Fedora 36 is going to follow upstream and Fedora 35 will be stuck in the last upstream major version it reached but with updates
This is to minimize the amount of testing.

## COPR repositories

The project needs three different COPR repositories in order to correctly track the impact of the next update.
- go-next -> the next version of Go build on top of the stable Fedora releases.
- go-next-packages -> All the packages that are available on the current stable Fedora releases using go-next.
- go-current-packages -> All the packages that are available on the current stable Fedora releases using the current go version.

## Creating the COPR repositories

[Configure the COPR client](https://copr.fedorainfracloud.org/api)

Create the three COPR repositories:
```bash
# go-current-packages
copr create go-current-packages --delete-after-days 10 --appstream=off --chroot fedora-35-aarch64 --chroot fedora-35-armhfp --chroot fedora-35-ppc64le --chroot fedora-35-s390x --chroot fedora-35-x86_64
parallel copr add-package-distgit go-current-packages --webhook-rebuild on --commit f35 --name -- $(repoquery --repo=fedora{,-source} --whatrequires golang --recursive | grep src$ | pkgname | sort | uniq)
parallel copr build-package go-current-packages --background --nowait --name -- $(repoquery --repo=fedora{,-source} --whatrequires golang --recursive | grep src$ | pkgname | sort | uniq)

# go-next
copr create go-next --appstream=off --delete-after-days 10 --chroot fedora-35-aarch64 --chroot fedora-35-armhfp --chroot fedora-35-ppc64le --chroot fedora-35-s390x --chroot fedora-35-x86_64
copr add-package-distgit go-next --webhook-rebuild on --commit rawhide --name golang
copr build-package go-next --background --nowait --name golang

# go-next-packages
copr create go-next-packages --delete-after-days 10 --repo='copr://alexsaezm/go-next' --appstream=off --chroot fedora-35-aarch64 --chroot fedora-35-armhfp --chroot fedora-35-ppc64le --chroot fedora-35-s390x --chroot fedora-35-x86_64
parallel copr add-package-distgit go-next-packages --webhook-rebuild on --commit f35 --name -- $(repoquery --repo=fedora{,-source} --whatrequires golang --recursive | grep src$ | pkgname | sort | uniq)
parallel copr build-package go-next-packages --background --nowait --name -- $(repoquery --repo=fedora{,-source} --whatrequires golang --recursive | grep src$ | pkgname | sort | uniq)
```

