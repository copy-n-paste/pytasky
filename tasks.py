import json
import os
from typing import List, Optional
from datetime import datetime

TASKS_FILE = 'task.json'

class Task:
    def __init__(self, name: str, description: str, time: str, date: str, repeat: str, status: str = 'pending'):
        self.name = name
        self.description = description
        self.time = time  # 'HH:MM:SS AM/PM'
        self.date = date  # 'DD-MM-YYYY'
        self.repeat = repeat  # One-time / Daily / Weekly / Monthly / Yearly
        self.status = status  # 'pending' or 'completed'

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'time': self.time,
            'date': self.date,
            'repeat': self.repeat,
            'status': self.status
        }

    @staticmethod
    def from_dict(data):
        return Task(
            name=data['name'],
            description=data['description'],
            time=data['time'],
            date=data['date'],
            repeat=data['repeat'],
            status=data.get('status', 'pending')
        )

def load_tasks() -> List[Task]:
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return [Task.from_dict(task) for task in data]
        except json.JSONDecodeError:
            return []

def save_tasks(tasks: List[Task]):
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump([task.to_dict() for task in tasks], f, indent=2)

def add_task(task: Task):
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)

def delete_task(task_name: str, date: Optional[str] = None, time: Optional[str] = None):
    tasks = load_tasks()
    tasks = [t for t in tasks if not (t.name == task_name and (date is None or t.date == date) and (time is None or t.time == time))]
    save_tasks(tasks)

def get_all_tasks() -> List[Task]:
    return load_tasks()

def mark_task_completed(task_name: str, date: Optional[str] = None, time: Optional[str] = None):
    tasks = load_tasks()
    for t in tasks:
        if t.name == task_name and (date is None or t.date == date) and (time is None or t.time == time):
            t.status = 'completed'
    save_tasks(tasks)

def get_tasks_by_status(status: str) -> List[Task]:
    return [t for t in load_tasks() if t.status == status] 