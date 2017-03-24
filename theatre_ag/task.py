"""
@author twsswt
"""
from .workflow import Idling


class Task(object):
    """
    Captures status information about a task to be performed by an actor.
    """

    def __init__(self, workflow, entry_point, args=(), parent=None):
        self.parent = parent
        self.workflow = workflow
        self.entry_point = entry_point
        self.args = args

        self.start_tick = None
        self.finish_tick = None

        self.sub_tasks = list()

    def initiate(self, start_tick):
        self.start_tick = start_tick

    def append_sub_task(self, workflow, entry_point, args=()):
        sub_task = Task(workflow, entry_point, args, parent=self)
        self.sub_tasks.append(sub_task)
        return sub_task

    def complete(self, finish_tick):
        self.finish_tick = finish_tick

    @property
    def initiated(self):
        return self.start_tick is not None

    @property
    def completed(self):
        return self.finish_tick is not None

    @property
    def non_idling_sub_tasks(self):
        return filter(lambda t: t.workflow is not Idling, self.sub_tasks)

    @property
    def last_non_idling_sub_task(self):
        return None if len(self.non_idling_sub_tasks) == 0 else self.non_idling_sub_tasks[-1]

    @property
    def last_non_idling_tick(self):
        if self.completed:
            return self.finish_tick
        else:
            if self.last_non_idling_sub_task is None:
                return self.start_tick
            else:
                return self.last_non_idling_sub_task.last_non_idling_tick

    def __repr__(self):

        start_tick = '?' if self.start_tick is None else str(self.start_tick)
        finish_tick = '?' if self.finish_tick is None else str(self.finish_tick)

        args = ','.join(map(lambda e: str(e), self.args))

        return '%s(%s)[%s->%s]' % (self.entry_point.func_name, args, start_tick, finish_tick)
