from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest

from taskflow import Scheduler, Taskflow, Workflow, WorkflowInstance, Task, TaskInstance
from taskflow.core.models import BaseModel

@pytest.fixture(scope='session')
def engine():
    return create_engine('postgresql://localhost/taskflow_test')

@pytest.fixture
def tables(engine):
    BaseModel.metadata.create_all(engine)
    yield
    BaseModel.metadata.drop_all(engine)

@pytest.fixture
def dbsession(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # put back the connection to the connection pool
    connection.close()

@pytest.fixture
def workflows(dbsession):
    workflow1 = Workflow(name='workflow1', active=True, schedule='0 6 * * *')
    workflow2 = Workflow(name='workflow2', active=True)
    dbsession.add(workflow1)
    dbsession.add(workflow2)

    task1 = Task(workflow=workflow1, name='task1', active=True)
    task2 = Task(workflow=workflow1, name='task2', active=True)
    task3 = Task(workflow=workflow1, name='task3', active=True)
    task4 = Task(workflow=workflow1, name='task4', active=True)

    task3.depends_on(task1)
    task3.depends_on(task2)
    task4.depends_on(task3)

    dbsession.add(task1)
    dbsession.add(task2)
    dbsession.add(task3)
    dbsession.add(task4)

    dbsession.commit()
    return [workflow1, workflow2]

def test_schedule_recurring_workflow(dbsession, workflows):
    taskflow = Taskflow()
    taskflow.add_workflows(workflows)
    scheduler = Scheduler(dbsession, taskflow, now_override=datetime(2017, 6, 3, 6))
    scheduler.run()

    workflow_instances = dbsession.query(WorkflowInstance).all()
    assert len(workflow_instances) == 1
    assert workflow_instances[0].status == 'queued'
    assert workflow_instances[0].scheduled == True
    assert workflow_instances[0].run_at == datetime(2017, 6, 4, 6)

    task_instances = dbsession.query(TaskInstance).all()
    assert len(task_instances) == 0

def test_start_workflow(dbsession, workflows):
    taskflow = Taskflow()
    taskflow.add_workflows(workflows)

    workflow_instance = WorkflowInstance(
            workflow='workflow1',
            scheduled=True,
            run_at=datetime(2017, 6, 3, 6),
            status='queued')
    dbsession.add(workflow_instance)
    dbsession.commit()

    scheduler = Scheduler(dbsession, taskflow, now_override=datetime(2017, 6, 3, 6, 0, 45))
    scheduler.run()

    dbsession.refresh(workflow_instance)
    assert workflow_instance.status == 'running'

    task_instances = dbsession.query(TaskInstance).all()
    assert len(task_instances) == 2
    for instance in task_instances:
        assert instance.task in ['task1','task2']
        assert instance.status == 'queued'

def test_workflow_running_no_change(dbsession, workflows):
    taskflow = Taskflow()
    taskflow.add_workflows(workflows)

    workflow_instance = WorkflowInstance(
            workflow='workflow1',
            scheduled=True,
            run_at=datetime(2017, 6, 3, 6),
            status='runnning')
    dbsession.add(workflow_instance)
    dbsession.commit()
    task_instance1 = TaskInstance(
        task='task1',
        workflow_instance=workflow_instance.id,
        status='running',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance2 = TaskInstance(
        task='task2',
        workflow_instance=workflow_instance.id,
        status='running',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    dbsession.add(task_instance1)
    dbsession.add(task_instance2)
    dbsession.commit()

    scheduler = Scheduler(dbsession, taskflow, now_override=datetime(2017, 6, 3, 6, 12))
    scheduler.run()

    task_instances = dbsession.query(TaskInstance).all()
    assert len(task_instances) == 2
    for instance in task_instances:
        assert instance.task in ['task1','task2']
        assert instance.status == 'running'

def test_workflow_next_step(dbsession, workflows):
    taskflow = Taskflow()
    taskflow.add_workflows(workflows)

    workflow_instance = WorkflowInstance(
            workflow='workflow1',
            scheduled=True,
            run_at=datetime(2017, 6, 3, 6),
            status='running')
    dbsession.add(workflow_instance)
    dbsession.commit()
    task_instance1 = TaskInstance(
        task='task1',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance2 = TaskInstance(
        task='task2',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    dbsession.add(task_instance1)
    dbsession.add(task_instance2)
    dbsession.commit()

    scheduler = Scheduler(dbsession, taskflow, now_override=datetime(2017, 6, 3, 6, 12))
    scheduler.run()

    task_instances = dbsession.query(TaskInstance).all()
    assert len(task_instances) == 3
    for instance in task_instances:
        assert instance.task in ['task1','task2','task3']
        if instance.task in ['task1','task2']:
            assert instance.status == 'success'
        elif instance.task == 'task3':
            assert instance.status == 'queued'

def test_workflow_success(dbsession, workflows):
    taskflow = Taskflow()
    taskflow.add_workflows(workflows)

    workflow_instance = WorkflowInstance(
            workflow='workflow1',
            scheduled=True,
            run_at=datetime(2017, 6, 3, 6),
            status='running')
    dbsession.add(workflow_instance)
    dbsession.commit()
    task_instance1 = TaskInstance(
        task='task1',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance2 = TaskInstance(
        task='task2',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance3 = TaskInstance(
        task='task3',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance4 = TaskInstance(
        task='task4',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    dbsession.add(task_instance1)
    dbsession.add(task_instance2)
    dbsession.add(task_instance3)
    dbsession.add(task_instance4)
    dbsession.commit()

    scheduler = Scheduler(dbsession, taskflow, now_override=datetime(2017, 6, 3, 6, 12))
    scheduler.run()

    dbsession.refresh(workflow_instance)
    assert workflow_instance.status == 'success'

    task_instances = dbsession.query(TaskInstance).all()
    assert len(task_instances) == 4
    for instance in task_instances:
        assert instance.task in ['task1','task2','task3','task4']
        assert instance.status == 'success'

def test_workflow_fail(dbsession, workflows):
    taskflow = Taskflow()
    taskflow.add_workflows(workflows)

    workflow_instance = WorkflowInstance(
            workflow='workflow1',
            scheduled=True,
            run_at=datetime(2017, 6, 3, 6),
            status='running')
    dbsession.add(workflow_instance)
    dbsession.commit()
    task_instance1 = TaskInstance(
        task='task1',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance2 = TaskInstance(
        task='task2',
        workflow_instance=workflow_instance.id,
        status='success',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    task_instance3 = TaskInstance(
        task='task3',
        workflow_instance=workflow_instance.id,
        status='failed',
        run_at=datetime(2017, 6, 3, 6, 0, 34),
        attempts=1)
    dbsession.add(task_instance1)
    dbsession.add(task_instance2)
    dbsession.add(task_instance3)
    dbsession.commit()

    scheduler = Scheduler(dbsession, taskflow, now_override=datetime(2017, 6, 3, 6, 12))
    scheduler.run()

    dbsession.refresh(workflow_instance)
    assert workflow_instance.status == 'failed'

    task_instances = dbsession.query(TaskInstance).all()
    assert len(task_instances) == 3
    for instance in task_instances:
        assert instance.task in ['task1','task2','task3']
        if instance.task in ['task1','task2']:
            assert instance.status == 'success'
        elif instance.task == 'task3':
            assert instance.status == 'failed'
