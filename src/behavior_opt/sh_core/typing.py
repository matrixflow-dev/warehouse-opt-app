from enum import IntEnum, Enum
from typing import Literal, NamedTuple, TypeAlias, TypedDict

# Define type aliases
Name: TypeAlias = str
PickDirection: TypeAlias = Literal["horizontal", "vertical", "on"]
Length: TypeAlias = int
Volume: TypeAlias = int
Amount: TypeAlias = int
PreconversionPosition: TypeAlias = list[int]


class Position(NamedTuple):
    row: int
    col: int


class AgentConfig(TypedDict):
    name: Name
    capacity: Volume
    pos: PreconversionPosition


class PickingTask(NamedTuple):
    name: Name
    pos: PreconversionPosition
    amount: Amount


class ItemConfig(TypedDict):
    name: Name
    pos: PreconversionPosition
    amount: Amount
    volume: Volume


class RackConfig(TypedDict):
    width: Length
    height: Length
    pos: PreconversionPosition
    pick_direction: PickDirection


class MapConfig(TypedDict):
    map_width: Length
    map_height: Length
    racks: list[RackConfig]

# Define constants
class Action(IntEnum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3
    NOOP = 4


class Direction(IntEnum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3
    NOOP = 4


FIELD_TYPE = dict(empty=0, rack=1, start=2, goal=3, agent=4, item=5, end_point=6)


ACTIONS = {
    Action.LEFT: Position(0, -1),
    Action.RIGHT: Position(0, 1),
    Action.UP: Position(-1, 0),
    Action.DOWN: Position(1, 0),
    Action.NOOP: Position(0, 0),
}

class Objective(Enum):
    """MCAのアクション"""

    START = 0
    PICK_UP = 1
    DROP_OFF = 2
    DOCK = 3
