
# Theatre_Ag: The Software Agent Theatre

A Python framework for multi-agent simulations, with a particular focus on modelling socio-technical systems.

# Contributors

Tim Storer<br/>
School of Computing Science, University of Glasgow.<br/>
GitHub ID: twsswt<br>
Email: [timothy.storer@glagow.ac.uk](mailto:timothy.storer@glagow.ac.uk)

Tom Wallis<br/>
School of Computing Science, University of Glasgow.<br/>
GitHub ID: probablytom<br>
Email: [twallisgm@gmail.com](mailto:twallisgm@gmail.com)

# Overview

## Terminology

Theatre_Ag follows a theatrical metaphor for its API and Architecture.  Core concepts in Theatre_Ag are:

 * **Clock** All activity in a Theatre_Ag simulation is executed with respect to a clock object that issues clock ticks
   up to a specified limit.

 * **Actor** A software agent with it's own thread of control.  Actor execution of activity is regulated by the ticks of
   clock.

 * **Setting** The problem domain 'physics' of the simulation environment.  Actors manipulate the setting when
   they execute workflows.

 * **Workflow** Task specifications implemented as Plain Old Python Classes.  Workflows describe the sequence of work
   items
   and decisions taken by actors when the workflow is executed and any state that is maintained during execution,
   allowing actors to influence the shared environment of a problem domain.
   Workflows can also be annotated with the costs of performing individual work items.

 * **Task** An instantiation of a workflow, comprising task meta data and an instance of workflow.  Individual tasks can
   be stateful and are permitted

 * **Cast** A collection of actors who will collaborate in a Theatre_Ag simulation.

 * **Episode** The specification of a cast of actors, and initial starting conditions (directions) that the cast will
   improvise from.

## Timing Model

The timing model in Theatre_Ag was designed with the simulation of socio-technical systems in mind. The timing model is
designed to represent the observation of time with respect to the
precision of a clock's tick.  The unit of a clock tick is domain specific, so could represent seconds, weeks or years.
All actors synchronize the execution of their tasks on the tick of a clock in the simulation.

The clock synchronization design is similar to turn based synchronisation models. It can be summarised as:

> "explicitly inter-tick strictly deterministic and intra-tick non-deterministic."

I don't know if there is a more formal term for this. In practice, this means that if an activity
can be specified to endure for an exact number of ticks for any number of concurrently executing activities.  If, for
example, activity *a* of duration 3 is initiated at time 1, and activity *b* of duration 1 is initiated at time 2,
then  activity *b* will finish at time 3 and activity *a* will finish at time 4.  However, if two activities are
 initiated or terminate at the same time, then the ordering of the initiation or
termination (and any consequent effect on the environment) is non-deterministic.  For example if activity *a* described
above only takes duration 2 then both activities will end at time 3 and the ordering of the termination is not
controlled by Theatre_Ag.  This contrasts with other turn based timing models that are strictly deterministic because
the order of agent execution during a turn can be pre-determined.

## Actor Task Processing

Actors are implemented as a threaded process managed by the <code>perform</code> method.

### Perform Control Loop

The perform method loops repeatedly as long as the actor still has tasks to be performed (<code>tasks_waiting</code> is
True) or the actor is waiting for more tasks.

Perform follows the following procedure in each loop:

1. Poll for a new task (<code>get_next_task</code>)
2. If a new task is available then:
   1. Log the task initiation.
   2. Calculate the cost of performing the task (<code>calculate_delay</code>) and wait for this number of ticks on the
      actor's clock.
   3. Execute the task
   4. Handle return values from task invocation (<code>handle_task_return</code>)
   5. Log the completion of the task
3. Else idle for one tick.

### Shutdown

Actors can be terminated if the <code>initiate_shutdown</code> method is invoked.  When this happens all remaining
available tasks are processed before shutdown.  The <code>wait_for_shutdown</code> method can be invoked once shutdown
is initiated and will block until all remaining tasks are processed. The Actor will also shutdown automatically if the
actor's clock reaches its maximum tick.  The actor will

### Configuration

The perform method behaviour can be configured in a sub-class by implementing the following three methods:

 * <code>get_next_task(self):Task</code>

   Called each time a new task is needed for invocation.  Implementing classes of Actor must override this method to
   provide a means of scheduling actor tasks.  Implementations of this method must return a <code>Task</code> object.

 * <code>handle_task_return(self, task, return_value):None</code>

   Called each time a task invocation completes.

 * <code>tasks_waiting(self):False</code>

   Called at the start of each perform loop to determine whether at least one task is available for invocation.

 * <code>calculate_delay(self, entry_point, workflow, args):int</code>

   Called immediately prior to executing a task to determine the number of ticks that must be observed before the
   entry point to a task is invoked.

The <code>TaskQueueActor</code> provides an example of how to override the default implementations of these methods.

# Tutorial

A single simulation run in Theatre_Ag is called an episode.  An episode needs a cast of actors and some directions, all
synchronized on a clock.  This tutorial describes the steps for creating an episode.

## Creating a Simulation Clock.

    clock = SynchronizingClock(max_ticks=5)

## Implementing the Cast

The abstract Actor class is responsible for executing tasks, synchronized on the Scenario clock.  However, it doesn't
have a mechanism for deciding how to schedule tasks, as this is left for implementation in the problem domain.  A simple
task queue oriented actor is provided with Theatre_Ag:

    actor = TaskQueueActor(clock)
    cast.add_member(actor)


## Directing the Cast with Workflows

A workflow is represented as a plain old Python class, comprising attributes (which can be used to store references to
state in the simulation domain) and methods for manipulating the state.  For example, a class to represent the possible
states of the cleanliness of your hands can be given as:

    class Hands(object):

        def _init__(self):
            self.clean = False
            self.soaped = False

The workflow for washing your hands (or anything else that can be washed) is defined using the following class.

    class Wash(object):

        is_workflow = True

        def __init__(self, washable):
            self.washable = washable

        def add_soap(self):
            self.washable.soaped = True

        def rinse(self):
            self.washable.soaped = False

        def scrub(self):
            if self.washable.soaped:
                self.washable.clean = True

        def wash(self):
            self.soap()
            self.scrub()
            self.rinse()

This workflow can be directly allocated to a TaskQueueActor.  The allocate_task method accepts a workflow instance and
an entry point, which should be a instance method reference on the same workflow instance.

    hands = Hands()
    wash = Wash(hands)
    actor.allocate_task(hands, wash.wash)

However, if you are dealing with an episode involving a large number of actors, it may be more convenient to specify
directions to a cast for the episode:

    class WashHandsDirection(object):

        def apply(self, cast):
            hands = Hands()
            wash = Wash(hands)
            cast.members[0].allocate_task(wash, wash.wash)

Workflows can be hierarchical, so it is possible to define (in the __init__ method) sub workflows that can be
invoked from the parent.  For example, suppose we decide that rinsing is a workflow that might be used in several
different workflows (perhaps a cleaning workflow that doesn't involve soap). Then we can separate out this part of the
overall workflow like this:

    class Rinse(object):

        is_workflow = True

        def __init__(self, washable):
            self.washable = washable

       def rinse(self):
            self.washable.soaped = False


    class Wash(object):

        is_workflow = True

        def __init__(self, washable):
            self.washable = washable
            self.rinse = Rinse(washable)

        def add_soap(self):
            self.washable.soaped = True

        def scrub(self):
            if self.washable.soaped:
                self.washable.clean = True

        def wash(self):
            self.soap()
            self.scrub()
            self.rinse.rinse()


## Playing an Episode and Gathering Results

Putting all this together, we can now define an episode of the problem domain and execute it as follows.

    direction = WashHandsDirection()
    episode = Episode(clock, cast, direction)
    episode.perform()

Data for analysis can be collected from the problem domain, since these are just plain old Python objects.  For example,

    print hands.clean

It is also possible to gather executed task history information from an Actor.  This information is stored in a
hierarchical tree of executed Task objects.  Task objects store the workflow, entry point, start and end times, as well
as any sub-tasks that were executed.  In the example episode above, for example, the actor will have exactly one wash
task in its history.  The wash task will have one rinse sub-task.

    print actor.task_history
    print actor.task_history[0].sub_tasks[0]
