from datetime import datetime

from marshmallow import Schema, fields
from marshmallow_sqlalchemy import ModelSchema, field_for
from flask_restful import Resource, abort
from restful_ben.resources import (
    RetrieveUpdateDeleteResource,
    QueryEngineMixin,
    CreateListResource
)

from taskflow import Taskflow, Workflow, WorkflowInstance, Task, TaskInstance

def to_list_response(data):
    count = len(data)
    return {
        'data': data,
        'count': count,
        'total_pages': 1 if count > 0 else 0,
        'page': 1 if count > 0 else 0,
    }

class SchedulableSchema(Schema):
    name = fields.String(dump_only=True)
    active = fields.Boolean(required=True)
    title = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    concurrency = fields.Integer(dump_only=True)
    sla = fields.Integer(dump_only=True)
    schedule = fields.String(dump_only=True)
    default_priority = fields.String(dump_only=True)
    start_date = fields.DateTime(dump_only=True)
    end_date = fields.DateTime(dump_only=True)

class TaskSchema(SchedulableSchema):
    workflow_name = fields.String(dump_only=True)

class WorkflowSchema(SchedulableSchema):
    pass

workflow_schema = WorkflowSchema()
workflows_schema = WorkflowSchema(many=True)

# workflow_authorization = authorization({
#     'normal': ['GET'],
#     'admin': ['POST','PUT','GET','DELETE']
# })

class WorkflowListResource(Resource):
    #method_decorators = [csrf.csrf_check, workflow_authorization, login_required]

    def get(self):
        self.taskflow.sync_db(self.session, read_only=True)
        workflows = sorted(self.taskflow.get_workflows(), key=lambda workflow: workflow.name)
        workflows_data = workflows_schema.dump(workflows).data
        return to_list_response(workflows_data)

class WorkflowResource(Resource):
    #method_decorators = [csrf.csrf_check, workflow_authorization, login_required]

    def get(self, workflow_name):
        self.taskflow.sync_db(self.session, read_only=True)
        workflow = self.taskflow.get_workflow(workflow_name)
        return workflow_schema.dump(workflow).data

    def put(self, workflow_name):
        input_workflow = workflow_schema.load(request.json or {})

        if input_workflow.errors:
            abort(400, errors=input_workflow.errors)

        self.taskflow.sync_db(self.session, read_only=True)
        workflow = self.taskflow.get_workflow(workflow_name)

        if not workflow:
            abort(404)

        workflow.active = input_workflow.data['active']
        self.session.commit()

        return workflow_schema.dump(workflow).data

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

class TaskListResource(Resource):
    #method_decorators = [csrf.csrf_check, workflow_authorization, login_required]

    def get(self):
        self.taskflow.sync_db(self.session, read_only=True)
        tasks = list(self.taskflow.get_tasks())
        for workflow in self.taskflow.get_workflows():
            tasks += workflow.get_tasks()
        tasks_sorted = sorted(tasks, key=lambda task: task.name)
        tasks_data = tasks_schema.dump(tasks_sorted).data
        return to_list_response(tasks_data)

class TaskResource(Resource):
    #method_decorators = [csrf.csrf_check, workflow_authorization, login_required]

    def get(self, task_name):
        self.taskflow.sync_db(self.session, read_only=True)
        task = self.taskflow.get_task(task_name)
        return task_schema.dump(task).data

    def put(self, task_name):
        input_task = task_schema.load(request.json or {})

        if input_task.errors:
            abort(400, errors=input_task.errors)

        self.taskflow.sync_db(self.session, read_only=True)
        task = self.taskflow.get_task(task_name)

        if not task:
            abort(404)

        task.active = input_task.data['active']
        self.session.commit()

        return task_schema.dump(task).data

## Instances

class WorkflowInstanceSchema(ModelSchema):
    class Meta:
        model = WorkflowInstance
        exclude = ['task_instances']

    id = field_for(WorkflowInstance, 'id', dump_only=True)
    status = field_for(WorkflowInstance, 'status', dump_only=True)
    scheduled = field_for(WorkflowInstance, 'scheduled', dump_only=True)
    created_at = field_for(WorkflowInstance, 'created_at', dump_only=True)
    updated_at = field_for(WorkflowInstance, 'updated_at', dump_only=True)

workflow_instance_schema = WorkflowInstanceSchema()
workflow_instances_schema = WorkflowInstanceSchema(many=True)

# workflow_instance_authorization = authorization({
#     'normal': ['GET'],
#     'admin': ['POST','PUT','GET','DELETE']
# })

class WorkflowInstanceResource(RetrieveUpdateDeleteResource):
    #method_decorators = [csrf.csrf_check, workflow_instance_authorization, login_required]
    single_schema = workflow_instance_schema
    model = WorkflowInstance

class WorkflowInstanceListResource(QueryEngineMixin, CreateListResource):
    #method_decorators = [csrf.csrf_check, workflow_instance_authorization, login_required]
    single_schema = workflow_instance_schema
    many_schema = workflow_instances_schema
    model = WorkflowInstance

class TaskInstanceSchema(ModelSchema):
    class Meta:
        model = TaskInstance

    id = field_for(TaskInstance, 'id', dump_only=True)
    status = field_for(TaskInstance, 'status', dump_only=True)
    scheduled = field_for(WorkflowInstance, 'scheduled', dump_only=True)
    created_at = field_for(TaskInstance, 'created_at', dump_only=True)
    updated_at = field_for(TaskInstance, 'updated_at', dump_only=True)

task_instance_schema = TaskInstanceSchema()
task_instances_schema = TaskInstanceSchema(many=True)

# task_instance_authorization = authorization({
#     'normal': ['GET'],
#     'admin': ['POST','PUT','GET','DELETE']
# })

class TaskInstanceResource(RetrieveUpdateDeleteResource):
    #method_decorators = [csrf.csrf_check, task_instance_authorization, login_required]
    single_schema = task_instance_schema
    model = TaskInstance

class TaskInstanceListResource(QueryEngineMixin, CreateListResource):
    #method_decorators = [csrf.csrf_check, task_instance_authorization, login_required]
    single_schema = task_instance_schema
    many_schema = task_instances_schema
    model = TaskInstance

class TaskflowRest(object):
    def __init__(self, app, session):
        pass
