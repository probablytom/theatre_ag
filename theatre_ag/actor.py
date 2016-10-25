import inspect

from Queue import Queue, Empty
from threading import RLock, Thread


class Task(object):

    def __init__(self, func, args):
        self.func = func
        self.args = args

    def __repr__(self):
        return "t_(%s, %s)" % (str(self.func), self.args)


def workflow(cost=0, enabled=True):
    def workflow_decorator(func):
        func.enabled = enabled
        func.cost = cost
        return func
    return workflow_decorator


class Actor(object):
    """
    Models the work behaviour of a self-directing entity.
    """

    def __init__(self, logical_name, clock):
        self.logical_name = logical_name
        self.clock = clock

        self.busy = RLock()
        self.wait_for_directions = True
        self.thread = Thread(target=self.perform)

        self.completed_tasks = []
        self.task_queue = Queue()

    def allocate_task(self, func, args=list()):
        self.task_queue.put(Task(func, args))

    def perform(self):
        """
        Repeatedly polls the actor's asynchronous work queue.
        """
        while self.wait_for_directions or not self.task_queue.empty():
            try:
                task = self.task_queue.get(block=False)
                if task is not None:
                    task.func(*task.args)
            except Empty:
                pass

    def __getattribute__(self, item):

        attribute = object.__getattribute__(self, item)

        if hasattr(attribute, 'enabled') and inspect.ismethod(attribute):
            def sync_wrap(*args, **kwargs):
                self.busy.acquire()

                reference_func = attribute.im_func

                cost = attribute.cost
                # TODO Pass function name and indicative cost to a cost calculation function.
                self._incur_cost(cost)

                result = reference_func(self, *args, **kwargs)
                self.completed_tasks.append((attribute, self.clock.current_tick))

                self.busy.release()
                return result

            return sync_wrap
        else:
            return attribute

    def start(self):
        self.thread.start()

    def shutdown(self):
        self.wait_for_directions = False
        self.thread.join()

    def _incur_cost(self, cost):
        start_tick = self.clock.current_tick
        self.clock.set_alarm(start_tick + cost)

    @workflow(1)
    def idle(self): pass
