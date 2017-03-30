class Cast(object):
    """
    A collection of actors who synchronize their actions on a single clock.
    """

    def __init__(self):
        self.members = list()

    def add_member(self, actor):
        self.members.append(actor)

    def improvise(self, directions):
        directions.apply(self.members)

    def start(self):
        for actor in self.members:
            actor.start()

    def shutdown(self):
        """
        Ends the performance by the cast by first initiating the shutdown of all member actors and then waiting for
        their termination.  This method can be safely called when the cast's clock is executed in a separate thread to
        the invocation.  Otherwise, <code>initiate_shutdown</code> should be called first, then a clock tick issued,
        followed by <code>wait_for_shutdown</code>.
        """
        self.initiate_shutdown()
        self.wait_for_shutdown()

    def initiate_shutdown(self):
        """
        Notifies all actors in the cast to begin shutdown.
        """
        for actor in self.members:
            actor.initiate_shutdown()

    def wait_for_shutdown(self):
        """
        Waits for all actors in the cast to complete shutdown.
        """
        for actor in self.members:
            actor.wait_for_shutdown()

    @property
    def last_tick(self):
        return reduce(max, map(lambda m: m.last_tick, self.members))

    def task_count(self, task):
        return sum(map(lambda actor: actor.task_count(task), self.members))
