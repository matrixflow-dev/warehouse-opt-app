from copy import copy
from typing import Iterator, Literal

from behavior_opt.sh_core.item import Item, Items
from behavior_opt.sh_core.task import Tasks
from behavior_opt.sh_core.typing import Name, Position


class Goal:
    def __init__(self, pos: Position, name: Name = "") -> None:
        self.pos = pos
        self.name = name
        self.pick_direction: Literal["on"] = "on"


class Agent:
    def __init__(
        self,
        pos: Position,
        name: Name = "",
        capacity: int = 5,
    ) -> None:
        self.pos = pos
        self.initial_pos = copy(pos)
        self.name = name
        self.goal: Goal = Goal(pos)
        self.volume = 0
        self.capacity = capacity
        self.having_items: Items = Items([])
        self.task_results  = None
        self.tasks: Tasks = Tasks([])
        self.target: Position | None = None

    def pick_up(self, item: Item) -> None:
        self.volume += item.volume
        self.having_items.add(item)
        item.current_owner = self
        item.is_picked = True

    def drop_off(self, item: Item) -> Item | None:
        self.volume -= item.volume
        drop_off_item = self.having_items.pop(item.name)
        assert drop_off_item is not None, "drop_off_item is None"
        drop_off_item.is_picked = False
        return drop_off_item

    def get_dist(self, pos: Position) -> int:
        """Calculate Manhattan distance between agent and pos."""
        return abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])


class Agents:
    def __init__(self, agents: list[Agent]) -> None:
        self._object_list = agents
        self._names = [agent.name for agent in agents]
        self._positions = [agent.pos for agent in agents]

    def index(self, name: Name) -> int:
        return self._names.index(name)

    @property
    def names(self) -> list[str]:
        return self._names[:]

    @property
    def positions(self) -> list[Position]:
        self._positions = [agent.pos for agent in self._object_list]
        return self._positions[:]

    def __iter__(self) -> Iterator[Agent]:
        return iter(self._object_list)

    def __len__(self) -> int:
        return len(self._object_list)

    def __getitem__(self, key: Name | int) -> Agent:
        if isinstance(key, Name):
            return self._object_list[self.index(key)]
        return self._object_list[key]

    def append(self, agent: Agent) -> None:
        self._object_list.append(agent)
        self._names.append(agent.name)
        self._positions.append(agent.pos)

    def remove(self, agent: Agent) -> None:
        index = self.index(agent.name)
        del self._object_list[index]
        del self._names[index]
        del self._positions[index]

    def reset(self) -> None:
        for a in self:
            a.pos = a.initial_pos
            a.goal = Goal(a.initial_pos)
            a.volume = 0
            a.having_items = Items([])
            a.task_results  = None
            a.tasks = Tasks([])
            a.target = None
        self._positions = [a.pos for a in self._object_list]
