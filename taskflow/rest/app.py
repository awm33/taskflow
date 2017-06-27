import os

import flask
from flask_restful import Api
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from taskflow.rest import resources
from taskflow.core.models import metadata, BaseModel

def create_app(taskflow_instance, connection_string=None):
    app = flask.Flask(__name__)
    app.config['DEBUG'] = os.getenv('DEBUG', False)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = connection_string or os.getenv('SQLALCHEMY_DATABASE_URI')

    db = SQLAlchemy(metadata=metadata, model_class=BaseModel)

    db.init_app(app)
    api = Api(app)
    CORS(app, supports_credentials=True)

    def apply_attrs(class_def, attrs):
        for key, value in attrs.items():
            setattr(class_def, key, value)
        return class_def

    attrs = {
        'session': db.session,
        'taskflow': taskflow_instance
    }

    with app.app_context():
        api.add_resource(apply_attrs(resources.WorkflowListResource, attrs), '/v1/workflows')
        api.add_resource(apply_attrs(resources.WorkflowResource, attrs), '/v1/workflows/<workflow_name>')

        api.add_resource(apply_attrs(resources.TaskListResource, attrs), '/v1/tasks')
        api.add_resource(apply_attrs(resources.TaskResource, attrs), '/v1/tasks/<task_name>')

        api.add_resource(apply_attrs(resources.WorkflowInstanceListResource, attrs), '/v1/workflow-instances')
        api.add_resource(apply_attrs(resources.WorkflowInstanceResource, attrs), '/v1/workflow-instances/<int:instance_id>')

        api.add_resource(apply_attrs(resources.RecurringWorkflowLastestResource, attrs), '/v1/workflow-instances/recurring-latest')

        api.add_resource(apply_attrs(resources.TaskInstanceListResource, attrs), '/v1/task-instances')
        api.add_resource(apply_attrs(resources.TaskInstanceResource, attrs), '/v1/task-instances/<int:instance_id>')

        api.add_resource(apply_attrs(resources.RecurringTaskLastestResource, attrs), '/v1/task-instances/recurring-latest')

    return app
