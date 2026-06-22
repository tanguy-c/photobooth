from django.conf import settings

from photobooth.backends.base import BaseBackend


def get_backend() -> BaseBackend:
    from photobooth.backends.rsync import RsyncBackend
    from photobooth.backends.webdav import WebDAVBackend

    backends = {
        "rsync": RsyncBackend,
        "webdav": WebDAVBackend,
    }
    backend_name = getattr(settings, "PHOTOBOOTH_BACKEND", "rsync")
    backend_cls = backends.get(backend_name)
    if backend_cls is None:
        raise ValueError(
            f"Unknown backend: {backend_name!r}. Choices: {', '.join(backends)}"
        )
    return backend_cls()
