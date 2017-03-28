import inspect
import traceback
import sys

from queue import Queue, Empty
from threading import Event, RLock, Thread

from .task import Task
from .workflow import allocate_workflow_to, Idling

PYTHON_VERSION = sys.version[0]


class OutOfTurnsException(Exception):

    def __init__(self, actor):
        self.actor = actor
    pass

    def __str__(self):
        return self.actor.logical_name, "out of turns after", self.actor.clock.current_tick, "ticks."


class Actor(object):
    """
    Models the work behaviour of a self-directing entity.  Actors can be assigned tasks described by workflows which are
    executed in synchronization with actor's clock.
    """

    def __init__(self, logical_name, clock):
        self.logical_name = logical_name
        self.clock = clock

        self.tick_received = Event()
        self.tick_received.clear()
        self.waiting_for_tick = Event()
        self.waiting_for_tick.clear()

        self.busy = RLock()
        self.wait_for_directions = True
        self.thread = Thread(target=self.perform)

        self.clock.add_tick_listener(self)

        self._task_history = list()
        self.current_task = None

        self.idling = Idling()
        allocate_workflow_to(self, self.idling, logging=False)

        self.next_turn = 0

    def log_task_initiation(self, workflow, entry_point, args):

        if self.current_task is not None:
            if self.current_task.initiated:
                self.current_task = self.current_task.append_sub_task(workflow, entry_point, args)

            self.current_task.initiate(self.clock.current_tick)

    def log_task_completion(self):
        if self.current_task is not None:
            self.current_task.complete(self.clock.current_tick)
            self.current_task = self.current_task.parent

    @property
    def task_history(self):
        task_history = filter(lambda task: task.workflow.logging is not False, self._task_history)
        if PYTHON_VERSION == '2':
            return task_history
        else:
            return list(task_history)

    @property
    def last_task(self):
        try:
            return self.task_history[-1]
        except IndexError:
            return None

    @property
    def last_tick(self):
        if self.last_task is None:
            return 0
        else:
            return self.last_task.last_non_idling_tick

    def task_count(self, task_func=None):

        def recursive_task_count(task_history):

            result = 0

            for completed_task in task_history:
                result += recursive_task_count(completed_task.sub_tasks)

                func = completed_task.entry_point.im_func if inspect.ismethod(completed_task.entry_point) \
                    else completed_task.entry_point

                if task_func is None or func.func_name == task_func.im_func.func_name:
                    result += 1

            return result

        return recursive_task_count(self.task_history)

    def handle_task_return(self, return_value):
        pass

    def get_next_task(self):
        """
        Implementing classes or mix ins should override this method.  By default, this method will cause an Actor to
        idle.
        :raises Empty: if no next task is available.
        """
        raise Empty()

    def tasks_waiting(self):
        """
        Implementing classes or mix ins should override this method.  By default, this method will return False.
        :return False:
        """
        return False

    def perform(self):
        """
        Repeatedly polls the actor's asynchronous work queue until the actor is shutdown.  Tasks in the work queue are
        executed synchronously until shutdown.  On shutdown, all remaining tasks in the queue are processed before
        termination.  Task execution will halt immediately if the actor's clock runs up to it's maximum tick count.
        """
        while self.wait_for_directions or self.tasks_waiting():
            task = None
            try:
                try:
                    task = self.get_next_task()
                    entry_point_name = task.entry_point.func_name

                    allocate_workflow_to(self, task.workflow)
                    task.entry_point = task.workflow.__getattribute__(entry_point_name)

                except Empty:
                    task = Task(self.idling, self.idling.idle)

                if task is not None:
                    self._task_history.append(task)
                    self.current_task = task
                    return_value = task.entry_point(*task.args)
                    self.handle_task_return(return_value)

            except OutOfTurnsException:
                break
            '''
            except Exception as e:
                if PYTHON_VERSION == '2':
                    print >> sys.stderr, "Warning, actor [%s] encountered exception [%s], in workflow [%s]." % \
                        (self.logical_name, str(e.message), str(task))
                else:
                    print("Warning, actor [%s] encountered exception [%s], in workflow [%s]." % \
                        (self.logical_name, str(e), str(task)), file=sys.stderr)
            '''

        # Ensure that clock can proceed for other listeners.
        self.clock.remove_tick_listener(self)
        self.waiting_for_tick.set()

    def start(self):
        self.thread.start()

    def shutdown(self):
        self.initiate_shutdown()
        self.wait_for_shutdown()

    def initiate_shutdown(self):
        self.wait_for_directions = False

    def wait_for_shutdown(self):
        self.thread.join()

    def incur_delay(self, delay):
        self.next_turn = max(self.next_turn, self.clock.current_tick)
        self.next_turn += delay

    def wait_for_turn(self):
        """
        A method that blocks while the actor's clock time is less than the time of the actor's next turn.
        """

        while self.clock.current_tick < self.next_turn:
            if self.clock.will_tick_again:
                self.waiting_for_tick.set()
                self.tick_received.wait()
                self.tick_received.clear()
            else:
                raise OutOfTurnsException(self)

    def notify_new_tick(self):
        self.waiting_for_tick.clear()
        self.tick_received.set()

    def __str__(self):
        return "a_%s" % self.logical_name

    def __repr__(self):
        return self.__str__()


class TaskQueueActor(Actor):
    """
    A simple actor class that receives executable tasks into a priority queue.
    """

    def __init__(self, logical_name,  clock):
        super(TaskQueueActor, self).__init__(logical_name, clock)
        self.task_queue = Queue()

    def get_next_task(self):
        return self.task_queue.get(block=False)

    def handle_task_return(self, return_value):
        pass

    def tasks_waiting(self):
        return not self.task_queue.empty()

    def allocate_task(self, workflow, entry_point, args=list()):

        allocated_task = Task(workflow, entry_point, args)
        self.task_queue.put(allocated_task)
        return allocated_task
