from copy import deepcopy
from enum import Enum

import numpy as np

from behavior_opt.sh_core import Agents, Position, Task, Tasks, World, Agent, Objective


class TaskAssignment:
    def __init__(self, world: World) -> None:
        self.agents = world.agents
        self.tasks = world.tasks
        self.assigned_tasks = {agent.name: Tasks([]) for agent in self.agents}
        self.actions = {agent.name: [] for agent in self.agents}
        self.current_task = {agent.name: None for agent in self.agents}
        self.current_action = {agent.name: None for agent in self.agents}

    def assign(self) -> None:
        """タスクの割り当てを行う"""
        raise NotImplementedError

    def set_target(self) -> None:
        """タスクの割り当てを行う"""
        actions: list[tuple[Objective, Task]] = []
        for agent_id, agent in enumerate(self.agents):
            if agent.target is None:
                assigned_tasks = self.assigned_tasks[agent.name]
                assigned_actions = self.actions[agent.name]
                if assigned_actions:
                    action = assigned_actions.pop(0)
                    if action == Objective.PICK_UP:
                        task = assigned_tasks.pop(0)
                        agent.target = task.item.end_point.pos
                        self.current_task[agent.name] = task
                        self.current_action[agent.name] = Objective.PICK_UP
                        actions.append((Objective.PICK_UP, task))
                    elif action == Objective.DROP_OFF:
                        task = assigned_tasks.pop(0)
                        agent.target = task.target_store_point.end_point.pos
                        self.current_task[agent.name] = task
                        self.current_action[agent.name] = Objective.DROP_OFF
                        actions.append((Objective.DROP_OFF, task))
                    elif action == Objective.DOCK:
                        agent.target = agent.goal.pos
                        actions.append((Objective.DOCK, ""))
                        self.current_task[agent.name] = None
                        self.current_action[agent.name] = Objective.DOCK
                        assigned_actions.append(Objective.DOCK)


class NearestTaskAssignment(TaskAssignment):
    def __init__(self, world: World) -> None:
        super().__init__(world)

    def assign(self) -> None:
        tasks = deepcopy(self.tasks)
        agents = deepcopy(self.agents)
        while len(tasks) > 0:
            for agent_id, agent in enumerate(agents):
                if len(tasks) == 0:
                    break
                task, _ = self.get_nearest_task(agent.pos, tasks)
                tmp_volume = agent.volume + task.item.volume
                if tmp_volume <= agent.capacity:
                    self.assigned_tasks[agent.name].append(task)
                    self.actions[agent.name].append(Objective.PICK_UP)
                    agent.volume = tmp_volume
                    agent.pos = task.item.end_point.pos
                    agent.having_items.add(task.item)
                    tasks.remove(task)
                else:
                    self.go_to_store_point(agent)
        for agent_id, agent in enumerate(agents):
            self.go_to_store_point(agent)
            self.actions[agents[agent_id].name].append(Objective.DOCK)

    def go_to_store_point(self, agent: Agent) -> None:
        while item := agent.having_items.pop(0):
            task: Task = self.tasks[item.name]
            self.assigned_tasks[agent.name].append(task)
            self.actions[agent.name].append(Objective.DROP_OFF)
            agent.volume -= task.item.volume
            agent.pos = task.target_store_point.end_point.pos

    def get_nearest_task(self, agent_pos: Position, tasks: Tasks) -> tuple[Task, int]:
        item_dists = [task.item.get_dist(agent_pos) for task in tasks]
        nearest_task = tasks[np.argmin(item_dists)]  # type: ignore
        nearest_task_dist = nearest_task.item.get_dist(agent_pos)
        return nearest_task, nearest_task_dist


class ManuallyTaskAssignment(TaskAssignment):
    def __init__(self, world: World):
        super().__init__(world)
        # self.assigned_tasks = {agent.name: Tasks([]) for agent in self.agents}
        # self.actions = {agent.name: [] for agent in self.agents}

    def assign(self, agent_name_list: list, task_list: list, action_list: list):
        """assigned_tasksとactionsを決める"""
        for agent_name, task, action in zip(agent_name_list, task_list, action_list):
            self.assigned_tasks[agent_name].append(task)
            self.actions[agent_name].append(action)

        for agent in self.agents:
            self.actions[agent.name].append(Objective.DOCK)
