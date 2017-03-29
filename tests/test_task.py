import unittest

from theatre_ag.task import Task
from theatre_ag.workflow import Idling


class TaskTestCase(unittest.TestCase):

    def setUp(self):

        def example_task():
            pass

        self.task = Task(example_task)

    def test_last_non_idling_tick_a(self):
        """
        The main task has been initiated.
        """
        self.task.initiate(1)
        self.assertEquals(1, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_b(self):
        """
        The main task has completed.
        """
        self.task.initiate(1)
        self.task.complete(2)
        self.assertEquals(2, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_c(self):
        """
        The main task has been initiated.
        One non-idling sub task has been initiated.
        """

        def example_sub_task():
            pass

        self.task.initiate(1)
        sub_task = self.task.append_sub_task(example_sub_task, ())
        sub_task.initiate(2)
        self.assertEquals(2, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_d(self):
        """
        The main task has been initiated.
        One non-idling sub task has completed.
        """
        def example_sub_task(): pass

        self.task.initiate(1)
        sub_task = self.task.append_sub_task(example_sub_task, ())
        sub_task.initiate(2)
        sub_task.complete(3)
        self.assertEquals(3, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_e(self):
        """
        The main task has been completed.
        One non-idling sub task has completed.
        """
        def example_sub_task(): pass

        self.task.initiate(1)
        sub_task = self.task.append_sub_task(example_sub_task, ())
        sub_task.initiate(2)
        sub_task.complete(3)
        self.task.complete(4)
        self.assertEquals(4, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_f(self):
        """
        The main task has been initiated.
        One idling sub task has initiated.
        """
        self.task.initiate(1)
        sub_task = self.task.append_sub_task(Idling.idle, Idling, ())
        sub_task.initiate(2)
        sub_task.complete(3)
        self.assertEquals(1, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_g(self):
        """
        The main task has been completed.
        One idling sub task has completed.
        """
        self.task.initiate(1)
        sub_task = self.task.append_sub_task(Idling, Idling.idle, ())
        sub_task.initiate(2)
        sub_task.complete(3)
        self.task.complete(4)
        self.assertEquals(4, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_h(self):
        """
        The main task has been initiated.
        One idling sub task has completed.
        One sub task has been initiated
        """
        self.task.initiate(1)
        idling_sub_task = self.task.append_sub_task(Idling.idle, Idling, ())
        idling_sub_task.initiate(2)
        idling_sub_task.complete(3)

        def example_sub_task(): pass

        sub_task = self.task.append_sub_task(example_sub_task, ())
        sub_task.initiate(4)
        self.assertEquals(4, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_i(self):
        """
        The main task has been initiated.
        One sub task has been completed.
        One idling sub task has completed.
        """
        def example_sub_task(): pass

        self.task.initiate(1)
        sub_task = self.task.append_sub_task(example_sub_task, ())
        sub_task.initiate(2)
        sub_task.complete(3)

        idling_sub_task = self.task.append_sub_task(Idling.idle, Idling, ())
        idling_sub_task.initiate(4)
        idling_sub_task.complete(5)

        self.assertEquals(3, self.task.last_non_idling_tick)

    def test_last_non_idling_tick_j(self):
        """
        The main task has been initiated.
        One sub task has been completed.
        One idling sub task  of the sub task has completed.
        """
        def example_sub_task(): pass

        self.task.initiate(1)
        sub_task = self.task.append_sub_task(example_sub_task, ())
        sub_task.initiate(2)
        sub_task.complete(3)

        idling_sub_task = sub_task.append_sub_task(Idling.idle, Idling, ())
        idling_sub_task.initiate(4)
        idling_sub_task.complete(5)

        self.assertEquals(3, self.task.last_non_idling_tick)


if __name__ == '__main__':
    unittest.main()
