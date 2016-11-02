import inspect

from Queue import Queue, Empty
from threading import Event, RLock, Thread


class Task(object):

    def __init__(self, func, args):
        self.func = func
        self.args = args

    def __repr__(self):
        return "t_(%s, %s)" % (str(self.func), self.args)


def default_cost(cost=0):
    def workflow_decorator(func):
        func.default_cost = cost
        return func
    return workflow_decorator


class CompletedTask(object):

    def __init__(self, func, start_tick, finish_tick):
        self.func = func
        self.start_tick = start_tick
        self.finish_tick = finish_tick

    def __str__(self):
        return "%s(%d->%d)" % (self.func.func_name, self.start_tick, self.finish_tick)

    def __repr__(self):
        return self.__str__()


class Workflow(object):

    def __init__(self, actor, logging=True):
        self.actor = actor
        self.logging = logging

    def __getattribute__(self, item):

        attribute = object.__getattribute__(self, item)

        if inspect.ismethod(attribute):

            def sync_wrap(*args, **kwargs):
                self.actor.busy.acquire()

                start_tick = self.actor.clock.current_tick

                # TODO Pass function name and indicative cost to a cost calculation function.
                if hasattr(attribute, 'default_cost'):
                    self.actor.incur_delay(attribute.default_cost)

                self.actor.wait_for_turn()

                result = attribute.im_func(self, *args, **kwargs)
                finish_tick = self.actor.clock.current_tick

                if self.logging:
                    self.actor.completed_tasks.append(CompletedTask(attribute, start_tick, finish_tick))

                self.actor.busy.release()

                return result

            return sync_wrap
        else:
            return attribute


class Idle(Workflow):
    """
    A workflow that allows an actor to waste a turn.
    """

    @default_cost(1)
    def idle(self): pass


class Actor(object):
    """
    Models the work behaviour of a self-directing entity.
    """

    def __init__(self, logical_name, clock):
        self.logical_name = logical_name
        self.clock = clock
        self.clock.add_tick_listener(self)

        self.busy = RLock()
        self.wait_for_directions = True
        self.thread = Thread(target=self.perform)

        self.completed_tasks = []
        self.task_queue = Queue()

        self.tick_received = Event()
        self.tick_received.clear()
        self.waiting_for_tick = Event()
        self.waiting_for_tick.clear()

        self.idle = Idle(self, logging=False)

        self.next_turn = 0

    def allocate_task(self, func, args=list()):
        self.task_queue.put(Task(func, args))

    @property
    def last_completed_task(self):
        index = len(self.completed_tasks)
        if index < 0:
            raise Empty()
        else:
            return self.completed_tasks[len(self.completed_tasks)-1]

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
                self.idle.idle()

        # Ensure that clock can proceed for other listeners.
        self.clock.remove_tick_listener(self)
        self.waiting_for_tick.set()

    def start(self):
        self.thread.start()

    def shutdown(self):
        self.wait_for_directions = False
        self.thread.join()

    def incur_delay(self, delay):
        self.next_turn = max(self.next_turn, self.clock.current_tick)
        self.next_turn += delay

    def wait_for_turn(self):
        while self.clock.current_tick < self.next_turn:
            self.waiting_for_tick.set()
            self.tick_received.wait()
            self.tick_received.clear()

    def notify_new_tick(self):
        self.tick_received.set()
        self.waiting_for_tick.clear()