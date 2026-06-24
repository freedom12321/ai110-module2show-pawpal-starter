from dataclasses import dataclass, field
from typing import List


@dataclass
class Owner:
    name: str
    available_time: int  # minutes per day
    preferences: List[str] = field(default_factory=list)

    def update_profile(self, name: str = None, available_time: int = None, preferences: List[str] = None):
        pass

    def get_availability(self) -> int:
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    energy_level: str  # e.g. "low", "medium", "high"

    def update_pet_info(self, **kwargs):
        pass

    def get_pet_summary(self) -> str:
        pass


@dataclass
class CareTask:
    name: str
    duration: int       # minutes
    priority: int       # 1 = highest
    category: str       # e.g. "feeding", "walk", "medication"
    required: bool = True

    def update_task(self, **kwargs):
        pass

    def get_task_summary(self) -> str:
        pass


class TaskManager:
    def __init__(self):
        self.tasks: List[CareTask] = []

    def add_task(self, task: CareTask) -> None:
        pass

    def edit_task(self, task_name: str, **kwargs) -> None:
        pass

    def delete_task(self, task_name: str) -> None:
        pass

    def get_tasks(self) -> List[CareTask]:
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: List[CareTask] = field(default_factory=list)
    skipped_tasks: List[CareTask] = field(default_factory=list)
    total_time_used: int = 0  # minutes

    def display_plan(self) -> None:
        pass

    def show_skipped_tasks(self) -> None:
        pass

    def get_summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, task_manager: TaskManager, owner: Owner):
        self.task_manager = task_manager
        self.owner = owner
        self.scheduled_tasks: List[CareTask] = []
        self.skipped_tasks: List[CareTask] = []

    def sort_tasks(self) -> List[CareTask]:
        pass

    def generate_plan(self) -> DailyPlan:
        pass

    def explain_plan(self) -> str:
        pass
