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
        api.add_resource(apply_attrs(resources.WorkflowListResource, attrs), '/workflows')
        api.add_resource(apply_attrs(resources.WorkflowResource, attrs), '/workflows/<workflow_name>')

        api.add_resource(apply_attrs(resources.TaskListResource, attrs), '/tasks')
        api.add_resource(apply_attrs(resources.TaskResource, attrs), '/tasks/<task_name>')

        api.add_resource(apply_attrs(resources.WorkflowInstanceListResource, attrs), '/workflow-instances')
        api.add_resource(apply_attrs(resources.WorkflowInstanceResource, attrs), '/workflow-instances/<int:instance_id>')

        api.add_resource(apply_attrs(resources.RecurringLastestResource, attrs), '/workflow-instances/recurring-latest')

        api.add_resource(apply_attrs(resources.TaskInstanceListResource, attrs), '/task-instances')
        api.add_resource(apply_attrs(resources.TaskInstanceResource, attrs), '/task-instances/<int:instance_id>')

    return app
