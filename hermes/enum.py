import enum
import json
from typing import Generic, TypeVar

from sqlalchemy.types import TEXT, TypeDecorator

# Type variable for enum.Enums
T = TypeVar("T", bound=enum.Enum)


class Enums(TypeDecorator, Generic[T]):
    impl = TEXT

    def __init__(self, enum_type: type[T], **kwargs):
        super().__init__(**kwargs)
        self.enum_type = enum_type

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps([v.value if isinstance(v, self.enum_type) else v for v in value])

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return [self.enum_type(v) for v in json.loads(value)]


class DayOfWeek(enum.Enum):
    Sun = "Sun"
    Mon = "Mon"
    Tue = "Tue"
    Wed = "Wed"
    Thu = "Thu"
    Fri = "Fri"
    Sat = "Sat"

    def next(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            index = 0
        return members[index]


class EmissionType(enum.Enum):
    A1A = "A1A"  # CW
    A3E = "A3E"  # AM speech
    F1B = "F1B"  # FSK (RTTY)
    J2B = "J2B"  # PSK (PSK31)
    J3C = "J3C"  # Facsimile for wefax
    J3E = "J3E"  # SSB speech
