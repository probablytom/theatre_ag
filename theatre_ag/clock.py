"""
@author twsswt
"""
from threading import Thread, Lock


class SynchronizingClock(object):

    def __init__(self, max_ticks=1):
        self.max_ticks = max_ticks

        self._ticks = 0

        self._tick_listeners = list()
        self._tick_listeners_lock = Lock()

        self.issue_ticks = True

        self._thread = Thread(target=self.tick_toc)

    @property
    def current_tick(self):
        return self._ticks

    @property
    def will_tick_again(self):
        return self.current_tick < self.max_ticks and self.issue_ticks

    def start(self):
        self._thread.start()

    def shutdown(self):
        self.issue_ticks = False
        self._thread.join()

    def wait_for_last_tick(self):
        self._thread.join()

    def add_tick_listener(self, listener):
        self._tick_listeners_lock.acquire()
        self._tick_listeners.append(listener)
        self._tick_listeners_lock.release()

    def remove_tick_listener(self, listener):
        self._tick_listeners_lock.acquire()
        self._tick_listeners.remove(listener)
        self._tick_listeners_lock.release()

    def tick(self):
        """
        Issues a tick once all registered tick listeners are waiting for them.
        """
        self._tick_listeners_lock.acquire()
        cached_tick_listeners = list(self._tick_listeners)
        self._tick_listeners_lock.release()
        print ("HERE")
        for tick_listener in cached_tick_listeners:
            print ("Waiting on ", tick_listener)
            tick_listener.waiting_for_tick.wait()

        self._ticks += 1

        for tick_listener in cached_tick_listeners:
            tick_listener.notify_new_tick()

    def tick_toc(self):
        while self.issue_ticks and self.current_tick < self.max_ticks:
            self.tick()

    def __str__(self):
        return "c(%d of %d)" % (self.current_tick, self.max_ticks)
