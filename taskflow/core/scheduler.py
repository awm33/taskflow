from datetime import datetime
from functools import reduce

from toposort import toposort

from .models import Workflow, WorkflowInstance, TaskInstance

class Scheduler(object):
    def __init__(self, session, taskflow, now_override=None):
        self.session = session
        self.taskflow = taskflow

        self.now_override = now_override

    def queue_workflow_task(self, workflow, task_name, workflow_instance, run_at=None):
        if run_at == None:
            run_at = self.now()

        print('queue_workflow_task')
        print(task_name)
        print(run_at)

        task_instance = TaskInstance(
            task=task_name,
            workflow_instance=workflow_instance.id,
            status='queued',
            run_at=run_at,
            attempts=0)
        self.session.add(task_instance)

    def queue_workflow_tasks(self, workflow_instance):
        workflow = self.taskflow.get_workflow(workflow_instance.workflow)
        dep_graph = workflow.get_dependencies_graph()
        dep_graph = list(toposort(dep_graph))
        print(dep_graph)

        results = self.session.query(TaskInstance)\
                    .filter(TaskInstance.workflow_instance == workflow_instance.id).all()
        workflow_task_instances = dict()
        for instance in results:
            workflow_task_instances[instance.task]

        ## dep_graph looks like [{'task2', 'task1'}, {'task3'}, {'task4'}]
        ## a list of sets where each set is a parallel step
        for step in dep_graph:
            total_in_step = len(step)
            total_complete = 0
            tasks_to_queue = []

            for task_name in step:
                if task_name in workflow_task_instances:
                    if workflow_task_instances[task_name].status == 'success':
                        total_complete += 1
                else:
                    tasks_to_queue.append(task_name)

            for task_name in tasks_to_queue:
                self.queue_workflow_task(workflow, task_name, workflow_instance)

            ## TODO: assert if len(tasks_to_queue) > 0 then total_complete < total_in_step ?

            if total_complete < total_in_step:
                break

        ## TODO: complete workflow
        ## TODO: fail workflow

    def queue_workflow(self, workflow, run_at):
        ## TODO: ensure this is in a transaction with queue_tasks ?
        workflow_instance = WorkflowInstance(
            workflow=workflow.name,
            scheduled=True,
            run_at=run_at,
            status='queued')
        self.session.add(workflow_instance)
        self.queue_workflow_tasks(workflow_instance)
        self.session.commit()

    def now(self):
        """Allows for dry runs and tests to use a specific datetime as now"""
        if self.now_override:
            return self.now_override
        return datetime.utcnow()

    def run(self):
        ## TODO:
        ## - fetch all active tasks not associated with a workflow
        ##      - next_run = schedule.next_run(last_run)
        ##      - if status is (null, not_running) and now >= next_run (from schedule)
        ##          - if number of tasks instances running < concurrency
        ##              - queue_task(task)
        ##      - if timedout
        ##          - if task.max_retries > task_instance.attempts
        ##              - queue task

        ## TODO: at some point, timeout queued workflow instances that have gone an interval past their run_at

        now = self.now()


        ##### Workflow scheduling

        workflows = filter(lambda workflow: workflow.active == True and workflow.schedule != None,
                           self.taskflow.get_fresh_workflows(self.session))

        for workflow in workflows:
            # try: !!! add this back after dev
                print(workflow.schedule)
                ## TODO: order by heartbeat instead ?
                most_recent_instance = self.session.query(WorkflowInstance)\
                                        .filter(WorkflowInstance.workflow == workflow.name,
                                                WorkflowInstance.scheduled == True)\
                                        .order_by(WorkflowInstance.run_at.desc())\
                                        .first()

                if most_recent_instance and most_recent_instance.status == 'running':
                    self.queue_workflow_tasks(most_recent_instance)
                    continue

                if not most_recent_instance: ## first run
                    next_run = workflow.next_run(base_time=now)
                else:
                    next_run = workflow.next_run(base_time=most_recent_instance.run_at)
                    last_run = workflow.last_run(base_time=now)
                    if last_run > next_run:
                        next_run = last_run

                print(next_run)

                if workflow.start_date and next_run < workflow.start_date or \
                    workflow.end_date and next_run > workflow.end_date:
                    continue

                if not most_recent_instance or most_recent_instance.status in ['success','failed']:
                    self.queue_workflow(workflow, next_run)
            # except Exception as e:
            #     ## TODO: switch to logger
            #     print('Exception scheduling Workflow "{}"'.format(workflow.name))
            #     print(e)

        ##### Task scheduling - tasks that do not belong to a workflow

        tasks = filter(lambda workflow: task.active == True and task.schedule != None,
                       self.taskflow.get_fresh_tasks(self.session))

        for task in tasks:
            print(task)
