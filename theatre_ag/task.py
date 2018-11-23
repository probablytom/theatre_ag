"""
@author twsswt
"""
import inspect
from .workflow import Idling
import sys

PYTHON_VERSION = sys.version[0]


class Task(object):
    """
    Captures status information about a task to be performed by an actor.
    """

    def __init__(self, entry_point, workflow=None, args=(), parent=None):

        self.entry_point = entry_point
        self.workflow = workflow

        if self.workflow is None:

            if hasattr(entry_point, 'im_self'):
                self.workflow = entry_point.im_self

            elif entry_point.func_closure is not None:
                self.workflow = entry_point.func_closure[1].cell_contents

            else:

                class AnonymousWorkflow(object):
                    is_workflow = True

                self.workflow = AnonymousWorkflow()
                if PYTHON_VERSION == '2':
                    setattr(self.workflow, entry_point.func_name, entry_point)
                else:
                    setattr(self.workflow, entry_point.__name__, entry_point)

        self.parent = parent
        self.args = args

        self.start_tick = None
        self.finish_tick = None

        self.sub_tasks = list()

    def initiate(self, start_tick):
        self.start_tick = start_tick

    def append_sub_task(self, entry_point, workflow=None, args=()):
        sub_task = Task(entry_point, workflow, args, parent=self)
        self.sub_tasks.append(sub_task)
        return sub_task

    def complete(self, finish_tick):
        self.finish_tick = finish_tick

    @property
    def siblings(self):
        return None if self.parent is None else self.parent.sub_tasks

    @property
    def is_last_sibling(self):
        return self.parent is not None and self.siblings.index(self) == len(self.siblings) - 1

    @property
    def has_siblings(self):
        return self.siblings is not None and len(self.siblings) > 0

    @property
    def entry_point_func (self):
        return self.entry_point.im_func if inspect.ismethod(self.entry_point) else self.entry_point

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

    @property
    def entry_point_name(self):
        return self.entry_point_func.func_name

    def __repr__(self):

        start_tick = '?' if self.start_tick is None else str(self.start_tick)
        finish_tick = '?' if self.finish_tick is None else str(self.finish_tick)

        args = ','.join(map(lambda e: str(e), self.args))

        if PYTHON_VERSION == '2':
            return '%s(%s)[%s->%s]' % (self.entry_point.func_name, args, start_tick, finish_tick)
        else:
            return '%s(%s)[%s->%s]' % (self.entry_point.__name__, args, start_tick, finish_tick)


def format_task_trees(tasks, indent=""):
    result = ""
    for task in tasks:
        result += format_task_tree(task, indent)
    return result


def format_task_tree(task, indent=""):

    arrow_mid = "+" if len(task.sub_tasks) > 0 else "-"
    arrow_tail = "-" if task.parent is None else "+" if task.is_last_sibling else "+"

    result = indent + arrow_tail + "-" + arrow_mid + "-> " + str(task) + "\n"

    indent += "| " if task.has_siblings and not task.is_last_sibling else "  "

    result += format_task_trees(task.sub_tasks, indent)

    return result
