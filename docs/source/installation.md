# Installation/Usage

Depending on the kind of user you are and your usecase, one or the other of the
installation/usage methods may be more or less appropriate.

### Docker

Usage through Docker will be most appropriate for those who:

- are looking to run it as a service which passively syncs subscribed series
- aren't familiar with python/python tooling

Sources:

- @Dockerhub:
  [chapter-sync](https://hub.docker.com/repository/docker/dancardin/chapter-sync)

The tool can be run (very basically) like so
`docker run -v chapter_sync.sqlite:/chapter-sync/chapter_sync.sqlite -itd chapter-sync`

or alternatively with `docker-compose`

```yaml
version: "3.8"

services:
  chapter-sync:
    image: chapter-sync
    restart: always
    volumes:
      - chapter_sync.sqlite:/chapter-sync/chapter_sync.sqlite
```

In either case you can `docker exec` into the container to interact with the
`chapter-sync` CLI (until such a time as there is a web UI).

### Python

Python installation will be most appropriate for those who:

- Will be locally running the CLI ad-hoc rather than as a "service"
- are familiar with python/python tooling

Chapter-sync can either be installed directly through PyPi

```bash
pip install chapter-sync
# or
pipx install chapter-sync
```

and then invoked with the CLI: `chapter-sync`
