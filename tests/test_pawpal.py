import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import CareTask, Pet, Priority


def test_mark_complete_changes_status():
    task = CareTask(name="Morning Walk", duration=30, priority=Priority.HIGH, category="walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=2, energy_level="high")
    assert len(pet.tasks) == 0
    pet.add_task(CareTask(name="Breakfast", duration=10, priority=Priority.HIGH, category="feeding"))
    assert len(pet.tasks) == 1
    pet.add_task(CareTask(name="Evening Walk", duration=20, priority=Priority.MEDIUM, category="walk"))
    assert len(pet.tasks) == 2
