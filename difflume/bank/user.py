from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class User:
    id: UUID = field(init=False, default_factory=uuid4)
    name: str
