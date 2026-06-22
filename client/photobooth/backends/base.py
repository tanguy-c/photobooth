import uuid
from abc import ABC, abstractmethod


class BaseBackend(ABC):
    @abstractmethod
    def upload(self, photo_uuid: uuid.UUID, datetime_str: str) -> None: ...
