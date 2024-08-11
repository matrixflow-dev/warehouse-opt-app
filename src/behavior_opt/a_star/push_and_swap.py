from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from typing import Any, Iterator, Literal, TypeAlias, overload

import networkx as nx
import numpy as np
from networkx.classes import Graph
from numpy.typing import NDArray

from behavior_opt.sh_core import Agent, Position

NIL = -1


class Path:
    def __init__(self, path: list[Position]) -> None:
        self._path: list[Position] = path

    def __len__(self) -> int:
        return len(self._path)

    @property
    def path(self) -> list[Position]:
        return self._path

    def remove(self, pos: Position) -> None:
        self._path.remove(pos)

    def append(self, pos: Position) -> None:
        self._path.append(pos)

    def empty(self) -> bool:
        return len(self._path) == 0

    def pop(self, i: int) -> Position:
        return self._path.pop(i)


Plan_t: TypeAlias = list[Position]


class Plan:
    def __init__(self, solution: list[Plan_t]) -> None:
        self.solution: list[Plan_t] = solution

    def __iter__(self) -> Iterator[Plan_t]:
        return iter(self.solution)

    def __len__(self) -> int:
        return len(self.solution)

    def __add__(self, other: Plan) -> Plan:
        return Plan(self.solution + other.solution)

    @overload
    def last(self) -> Plan_t:
        ...

    @overload
    def last(self, agent_id: int) -> Position:
        ...

    def last(self, agent_id: int | None = None) -> Position | Plan_t:
        if agent_id is None:
            return self.solution[self.get_makespan()].copy()
        else:
            return self.solution[self.get_makespan()][agent_id]

    def empty(self) -> bool:
        return len(self.solution) == 0

    def append(self, path: Plan_t) -> None:
        self.solution.append(path)

    def get_makespan(self) -> int:
        return len(self.solution) - 1


class PushAndSwap:
    def __init__(
        self,
        agents: list[Agent],
        world_map: NDArray[Any],
        enable_dist_init: bool = True,
    ) -> None:
        self.SOLVER_NAME = "PushAndSwap"
        self._fig_compress: bool = True
        self._disable_dist_init: bool = False
        self.agents = agents
        self.n_agents = len(agents)
        self.graph = self.create_graph(world_map)
        self.enable_dist_init = enable_dist_init

    def run(self):
        assert None not in [agent.target for agent in self.agents], "invalid target"
        self._nodes_with_many_neighbors: list[Position] = []
        self.plan = Plan([[agent.pos for agent in self.agents]])
        # occupancy
        self.occupied_now: defaultdict[Position, int] = defaultdict(lambda: NIL)
        nx.set_node_attributes(self.graph, name="occupied", values=NIL)  # type: ignore
        for agent_id, sol_per_agent in enumerate(self.plan.last()):
            self.occupied_now[sol_per_agent] = agent_id
        # pre-processing
        self.find_nodes_with_many_neighbors()
        # nodes with agents at goals
        nodes_U: list[Position] = []
        agent_ids = list(range(self.n_agents))
        # prioritization
        if self.enable_dist_init:
            agent_ids.sort(
                key=lambda agent_id: nx.shortest_path_length(self.graph, self.agents[agent_id].pos, self.agents[agent_id].target)  # type: ignore
            )

        # if target is same, change target
        tmp_targets = [agent.target for agent in self.agents]
        other_agents_target: list[Position] = []
        for agent_id in agent_ids:
            if self.agents[agent_id].target != self.agents[agent_id].pos:
                while self.agents[agent_id].target in other_agents_target:
                    self.agents[agent_id].target = Position(
                        *nx.shortest_path(  # type: ignore
                            self.graph,
                            self.agents[agent_id].pos,
                            self.agents[agent_id].target,
                        )[-2]
                    )
            other_agents_target.append(self.agents[agent_id].target)
        # main loop
        for j in range(self.n_agents):
            agent_id = agent_ids[j]
            print(
                f"agent-{agent_id} starts planning, makespan: {len(self.plan)},progress: {j+1}/{self.n_agents}"
            )
            while self.plan.last(agent_id) != self.agents[agent_id].target:
                if not self.push(agent_id, nodes_U):
                    print(f"swap required, timestep: {len(self.plan)}")
                    if not self.swap(agent_id, nodes_U):
                        return
            nodes_U.append(self.plan.last(agent_id))
            # !ここに時間制限を入れる
        for agent_id, target in enumerate(tmp_targets):
            self.agents[agent_id].target = target
        if self._fig_compress:
            print("compressing plan")
            print("before:", self.plan.get_makespan())
            self.plan = self.compress(self.plan, finish_func=any)
            print("after:", self.plan.get_makespan())
            targets = [agent.target for agent in self.agents]

        finished_agents: list[int] = []
        for agent_id, is_finished in enumerate(
            [Position(*p) == t for p, t in zip(self.plan.last(), targets)]
        ):
            if is_finished:
                print(f"agent-{agent_id} finished")
                self.agents[agent_id].target = None
                finished_agents.append(agent_id)

        return self.plan.solution, finished_agents

    def push(self, agent_id: int, nodes_U: list[Position]) -> bool:
        if self.plan.last(agent_id) == self.agents[agent_id].target:
            return True
        # create shortest path
        p_star = self.get_shortest_path(agent_id, self.plan.last(agent_id))
        p_star.pop(0)
        if p_star.empty():
            return False  # for safety

        node_v = p_star.path[0]
        while self.plan.last(agent_id) != self.agents[agent_id].target:
            while self.occupied_now[node_v] == NIL:
                self.plan, self.occupied_now = self.update_plan(
                    self.plan, agent_id, node_v, self.occupied_now
                )
                p_star.remove(node_v)
                if p_star.empty():
                    return True
                node_v = p_star.path[0]
            obstacles = nodes_U.copy()
            obstacles.append(self.plan.last(agent_id))
            is_empty, self.plan, self.occupied_now = self.push_toward_empty_node(
                self.plan, node_v, obstacles, self.occupied_now
            )
            if not is_empty:
                return False

        return True

    def swap(self, agent1_id: int, nodes_U: list[Position]):
        p_star = self.get_shortest_path(agent1_id, self.plan.last(agent1_id))
        if len(p_star) <= 1:
            return True
        agent2_id = self.occupied_now[p_star.path[1]]
        if agent2_id == NIL:
            return True

        c_before = self.plan.last()
        success = False
        swap_vertices = self._nodes_with_many_neighbors.copy()

        # sort, make swap operation easy
        node_v: Position = p_star.path[0]

        def manhattan_dist(pos: Position):
            return abs(pos[0] - node_v[0]) + abs(pos[1] - node_v[1])

        swap_vertices.sort(key=lambda v: manhattan_dist(v))
        swap_vertices.pop(0)
        while (len(swap_vertices) != 0) and not success:
            node_v = swap_vertices.pop(0)
            p: Path = Path(nx.shortest_path(self.graph, self.plan.last(agent1_id), node_v))  # type: ignore
            tmp_plan: Plan = Plan([])
            tmp_plan.append(self.plan.last())
            tmp_occupied_now = self.occupied_now.copy()
            can_multi_push, tmp_plan, tmp_occupied_now = self.multi_push(
                tmp_plan,
                agent1_id,
                agent2_id,
                p,
                tmp_occupied_now,
            )
            if (node_v == self.plan.last(agent1_id)) or can_multi_push:
                is_clear, tmp_plan, tmp_occupied_now = self.clear(
                    tmp_plan, node_v, agent1_id, agent2_id, tmp_occupied_now
                )
                if is_clear:
                    success = True
        if not success:
            return False

        for i in range(self.n_agents):
            self.occupied_now[self.plan.last(i)] = NIL
        self.plan += tmp_plan
        for i in range(self.n_agents):
            self.occupied_now[self.plan.last(i)] = i

        self.execute_swap(agent1_id, agent2_id)
        reversed_tmp_plan = Plan([])
        makespan = tmp_plan.get_makespan()
        for t in range(0, makespan + 1)[::-1]:
            c = tmp_plan.solution[t].copy()
            c[agent1_id], c[agent2_id] = c[agent2_id], c[agent1_id]
            reversed_tmp_plan.append(c)

        for i in range(self.n_agents):
            self.occupied_now[self.plan.last(i)] = NIL
        self.plan += reversed_tmp_plan
        for i in range(self.n_agents):
            self.occupied_now[self.plan.last(i)] = i

        c_after = self.plan.last()
        for i in range(self.n_agents):
            assert not (
                (i == agent2_id and c_after[agent2_id] != c_before[agent1_id])
                or (i == agent1_id and c_after[agent1_id] != c_before[agent2_id])
                or (i != agent1_id and i != agent2_id and c_before[i] != c_after[i])
            ), "invalid swap operation"
            assert (
                (i != agent2_id or c_after[agent2_id] == c_before[agent1_id])
                and (i != agent1_id or c_after[agent1_id] == c_before[agent2_id])
                and (i == agent1_id or i == agent2_id or c_before[i] == c_after[i])
            ), "invalid swap operation"
        print(
            f"agent-{agent1_id}, agent-{agent2_id} swap locations {c_before[agent1_id]} -> {c_after[agent1_id]}"
        )
        if self.agents[agent2_id].target in nodes_U:
            return self.resolve(agent1_id, agent2_id, nodes_U)
        return True

    def resolve(self, agent1_id: int, agent2_id: int, nodes_U: list[Position]):
        print(f"resolve: {agent1_id}")
        # create shortest path
        assert self.plan.last(agent1_id) in nx.neighbors(
            self.graph, self.plan.last(agent2_id)
        ), "invalid resolve operation"
        ideal_loc_s = self.plan.last(agent1_id)

        while self.occupied_now[ideal_loc_s] != NIL:
            _agent1_id = self.occupied_now[ideal_loc_s]
            if _agent1_id == NIL:
                break
            # case 1. push
            path = self.get_shortest_path(_agent1_id, ideal_loc_s)
            assert not path.empty(), "never-happen situations"
            if self.occupied_now[path.path[1]] != NIL:
                obstacles = nodes_U.copy()
                obstacles.append(self.plan.last(agent2_id))
                obstacles.append(self.plan.last(_agent1_id))
                (is_empty, self.plan, self.occupied_now,) = self.push_toward_empty_node(
                    self.plan, path.path[1], obstacles, self.occupied_now
                )
                if not is_empty:
                    print(f"recursive swap is called for {agent1_id}")
                    if not self.swap(_agent1_id, nodes_U):
                        return False
                else:
                    self.plan, self.occupied_now = self.update_plan(
                        self.plan, _agent1_id, path.path[1], self.occupied_now
                    )
            else:
                self.plan, self.occupied_now = self.update_plan(
                    self.plan, _agent1_id, path.path[1], self.occupied_now
                )

        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent2_id, ideal_loc_s, self.occupied_now
        )
        return True

    def multi_push(
        self,
        plan: Plan,
        agent1_id: int,
        agent2_id: int,
        path: Path,
        occupied_now: defaultdict[Position, int],
    ) -> tuple[bool, Plan, defaultdict[Position, int]]:
        p_size = len(path)
        assert p_size > 0, "path is empty"
        # case 1
        if plan.last(agent2_id) != path.path[1]:
            for i in range(1, p_size):
                # agent1 tries to reserve node_v
                if occupied_now[path.path[i]] != NIL:
                    is_empty, plan, occupied_now = self.push_toward_empty_node(
                        plan, path.path[i], [plan.last(agent2_id)], occupied_now
                    )
                    if not is_empty:
                        return False, plan, occupied_now
                plan, occupied_now = self.update_plan(
                    plan, agent1_id, path.path[i], occupied_now
                )
                plan, occupied_now = self.update_plan(
                    plan, agent2_id, path.path[i - 1], occupied_now
                )
        # case 2
        else:
            for i in range(2, p_size):
                node_v = path.path[i]
                if occupied_now[node_v] != NIL:
                    is_empty, plan, occupied_now = self.push_toward_empty_node(
                        plan, node_v, [plan.last(agent1_id)], occupied_now
                    )
                    if not is_empty:
                        return False, plan, occupied_now
                plan, occupied_now = self.update_plan(
                    plan, agent2_id, path.path[i], occupied_now
                )
                plan, occupied_now = self.update_plan(
                    plan, agent1_id, path.path[i - 1], occupied_now
                )
            is_empty, plan, occupied_now = self.push_toward_empty_node(
                plan, path.path[p_size - 1], [plan.last(agent1_id)], occupied_now
            )
            if not is_empty:
                return False, plan, occupied_now
            plan, occupied_now = self.update_plan(
                plan, agent1_id, path.path[p_size - 1], occupied_now
            )
        return True, plan, occupied_now

    def check_consistency(self, plan: Plan, occupied_now: defaultdict[Position, int]):
        c = plan.last()
        for agent_id in range(self.n_agents):
            assert occupied_now[c[agent_id]] == agent_id, "check consistency"

    # clear operation
    def clear(
        self,
        plan: Plan,
        node_v: Position,
        agent1_id: int,
        agent2_id: int,
        occupied_now: defaultdict[Position, int],
    ):
        print(f"clear operation for {agent1_id} at {node_v}")

        def get_unoccupied_nodes() -> list[Position]:
            return [
                node
                for node in self.graph.neighbors(node_v)  # type: ignore
                if occupied_now[node] == NIL  # type: ignore
            ]

        unoccupied_nodes = get_unoccupied_nodes()
        # trivial case
        if len(unoccupied_nodes) >= 2:
            return True, plan, occupied_now
        # case 1
        tmp_plan = deepcopy(plan)
        tmp_occupied_now = deepcopy(occupied_now)
        for node_u in self.graph.neighbors(node_v):  # type: ignore
            unoccupied_nodes = get_unoccupied_nodes()
            if node_u in unoccupied_nodes:
                continue
            obstacles = unoccupied_nodes.copy()
            obstacles.append(plan.last(agent1_id))
            obstacles.append(plan.last(agent2_id))
            self.check_consistency(plan, occupied_now)
            is_empty, plan, occupied_now = self.push_toward_empty_node(
                plan, node_u, obstacles, occupied_now
            )
            if is_empty:
                if len(get_unoccupied_nodes()) >= 2:
                    return True, plan, occupied_now
        plan = tmp_plan
        occupied_now = tmp_occupied_now
        # case 2
        last_loc_s = plan.last(agent2_id)
        for node_u in self.graph.neighbors(node_v):  # type: ignore
            node_u: Position
            unoccupied_nodes = get_unoccupied_nodes()
            if node_u in unoccupied_nodes:
                continue
            disturbing_agent = occupied_now[node_u]
            for node_w in unoccupied_nodes:
                obstacles = get_unoccupied_nodes()
                obstacles.append(node_u)
                obstacles.append(node_v)
                obstacles.append(node_w)
                is_empty, plan, occupied_now = self.push_toward_empty_node(
                    plan, last_loc_s, obstacles, occupied_now
                )
                if is_empty:
                    plan, occupied_now = self.update_plan(
                        plan, agent1_id, last_loc_s, occupied_now
                    )
                    plan, occupied_now = self.update_plan(
                        plan, disturbing_agent, node_v, occupied_now
                    )
                    plan, occupied_now = self.update_plan(
                        plan, disturbing_agent, node_w, occupied_now
                    )
                    plan, occupied_now = self.update_plan(
                        plan, agent1_id, node_v, occupied_now
                    )
                    plan, occupied_now = self.update_plan(
                        plan, agent2_id, last_loc_s, occupied_now
                    )

                    obstacles2 = get_unoccupied_nodes()
                    obstacles2.append(node_v)
                    obstacles2.append(last_loc_s)
                    is_empty, plan, occupied_now = self.push_toward_empty_node(
                        plan, node_w, obstacles2, occupied_now
                    )
                    if is_empty:
                        if len(get_unoccupied_nodes()) >= 2:
                            return True, plan, occupied_now
                        break
        return False, plan, occupied_now

    def execute_swap(
        self,
        agent1_id: int,
        agent2_id: int,
    ):
        empty1: Position | None = None
        empty2: Position | None = None
        node_v = self.plan.last(agent1_id)
        last_loc_s = self.plan.last(agent2_id)
        for u in self.graph.neighbors(node_v):  # type: ignore
            if self.occupied_now[u] == NIL:  # type: ignore
                if empty1 is None:
                    empty1: Position = u
                elif empty2 is None:
                    empty2: Position = u
                    break
        assert empty2 is not None, "execute swap, failed to clear"
        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent1_id, empty1, self.occupied_now
        )
        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent2_id, node_v, self.occupied_now
        )
        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent2_id, empty2, self.occupied_now
        )
        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent1_id, node_v, self.occupied_now
        )
        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent1_id, last_loc_s, self.occupied_now
        )
        self.plan, self.occupied_now = self.update_plan(
            self.plan, agent2_id, node_v, self.occupied_now
        )

    def update_plan(
        self,
        plan: Plan,
        agent_id: int,
        next_node: Position,
        occupied_now: defaultdict[Position, int],
    ):
        assert occupied_now[plan.last(agent_id)] == agent_id, "invalid update"
        assert occupied_now[next_node] == NIL, "vertex conflict"

        # update occupancy
        occupied_now[plan.last(agent_id)] = NIL
        occupied_now[next_node] = agent_id
        # update plan
        c = plan.last()
        c[agent_id] = next_node
        plan.append(c)

        return plan, occupied_now

    def push_toward_empty_node(
        self,
        plan: Plan,
        node_v_current: Position,
        obstacles: list[Position],
        occupied_now: defaultdict[Position, int],
    ):
        v_empty = self.get_nearest_empty_node(node_v_current, obstacles, occupied_now)
        if v_empty is None:
            return False, plan, occupied_now

        def get_path() -> list[Position]:
            G = self.graph.copy()
            for obstacle in obstacles:
                if obstacle in G:
                    G.remove_node(obstacle)
            return nx.shortest_path(G, node_v_current, v_empty)  # type: ignore

        p: list[Position] = get_path()  # type: ignore
        for i in reversed(range(1, len(p))):
            assert occupied_now[p[i - 1]] != NIL, "node must be occupied"
            plan, occupied_now = self.update_plan(
                plan, occupied_now[p[i - 1]], p[i], occupied_now
            )
        return True, plan, occupied_now

    def get_shortest_path(self, agent_id: int, node_s: Position) -> Path:
        path = [node_s]
        node_g = self.agents[agent_id].target

        while path[-1] != node_g:
            node_v = path[-1]
            next_node: Position | None = None
            pre_node: Position | None = None
            for node_u in self.graph.neighbors(node_v):  # type: ignore
                node_u: Position
                if pre_node is None:
                    pre_node = node_u
                c_a: int = nx.shortest_path_length(self.graph, node_u, node_g)  # type: ignore
                c_b: int = nx.shortest_path_length(self.graph, pre_node, node_g)  # type: ignore
                if c_a != c_b:
                    next_node = node_u if c_a < c_b else pre_node
                    pre_node = next_node
                    continue
                o_a = self.occupied_now[node_u]
                o_b = self.occupied_now[pre_node]
                if o_a != o_b:
                    next_node = node_u if o_a < o_b else pre_node
                    pre_node = next_node
                    continue
                next_node = pre_node
            assert next_node is not None, "get shortest path failed"
            path.append(next_node)
        return Path(path)

    def get_nearest_empty_node(
        self,
        node_v: Position,
        obstacles: list[Position],
        occupied_now: defaultdict[Position, int],
    ) -> Position:
        agent_id = occupied_now[node_v]
        agent = self.agents[agent_id]
        v_empty: Position | None = None
        open_: deque[Position] = deque([node_v])
        close_: defaultdict[Position, bool] = defaultdict(lambda: False)
        for obs in obstacles:
            close_[obs] = True
        while open_:
            node_u = open_.popleft()
            if close_[node_u]:
                continue
            close_[node_u] = True
            if occupied_now[node_u] == NIL:
                v_empty = node_u
                break
            nodes_C: list[Position] = []
            for neighbor in self.graph.neighbors(node_u):  # type: ignore
                if close_[neighbor]:  # type: ignore
                    continue
                nodes_C.append(neighbor)  # type: ignore
            nodes_C.sort(key=lambda node: agent.get_dist(node))
            open_.extend(nodes_C)
        return v_empty

    def find_nodes_with_many_neighbors(self):
        self._nodes_with_many_neighbors = []
        for node, degree in self.graph.degree():  # type: ignore
            node: Position
            degree: int
            if degree >= 3:
                self._nodes_with_many_neighbors.append(node)

    def compress(self, plan: Plan, finish_func: Literal[all, any] = any):
        temp_orders: dict[Position, deque[int]] = {node: deque([]) for node in self.graph.nodes}  # type: ignore
        makespan = plan.get_makespan()
        for t in range(makespan + 1):
            for agent_id, agent in enumerate(self.agents):
                node_v = plan.solution[t][agent_id]
                if (
                    len(temp_orders[node_v]) == 0
                    or node_v != plan.solution[t - 1][agent_id]
                ):
                    temp_orders[node_v].append(agent_id)
        new_plan = Plan([])
        new_plan.append(plan.solution[0])
        internal_clock = [0 for _ in range(self.n_agents)]
        targets = [agent.target for agent in self.agents]

        while not finish_func([p == t for p, t in zip(new_plan.last(), targets)]):
            plan_t: Plan_t = []
            for agent_id, agent in enumerate(self.agents):
                t = internal_clock[agent_id]
                if t == makespan:
                    plan_t.append(new_plan.last(agent_id))
                    continue
                v_current = plan.solution[t][agent_id]
                while t < makespan and v_current == plan.solution[t + 1][agent_id]:
                    t += 1
                internal_clock[agent_id] = t

                if t == makespan:
                    plan_t.append(new_plan.last(agent_id))
                    continue

                v_next = plan.solution[t + 1][agent_id]
                if temp_orders[v_next][0] == agent_id:
                    plan_t.append(v_next)
                    temp_orders[v_current].popleft()
                    internal_clock[agent_id] = t + 1
                else:
                    plan_t.append(new_plan.last(agent_id))
            new_plan.append(plan_t)
        return new_plan

    def create_graph(self, map_: NDArray[np.uint8]):
        G: Graph = nx.grid_2d_graph(map_.shape[0], map_.shape[1])  # type: ignore
        for i in range(map_.shape[0]):
            for j in range(map_.shape[1]):
                if map_[i, j] == 1:
                    G.remove_node((i, j))  # type: ignore
        return G
