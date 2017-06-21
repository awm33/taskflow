import pytest

from shared_fixtures import *
from utils import json_call, dict_contains, iso_regex

def test_list_workflows(app):
    test_client = app.test_client()

    response = json_call(test_client.get, '/workflows')
    assert response.status_code == 200
    assert response.json['count'] == 2
    assert response.json['page'] == 1
    assert response.json['total_pages'] == 1
    assert len(response.json['data']) == 2
    assert dict_contains(response.json['data'][0], {
        'name': 'workflow1',
        'active': True,
        'title': None,
        'description': None,
        'schedule': '0 6 * * *',
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })
    assert dict_contains(response.json['data'][1], {
        'name': 'workflow2',
        'active': True,
        'title': None,
        'description': None,
        'schedule': None,
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })

def test_get_workflow(app):
    test_client = app.test_client()

    response = json_call(test_client.get, '/workflows/workflow1')
    assert response.status_code == 200
    assert dict_contains(response.json, {
        'name': 'workflow1',
        'active': True,
        'title': None,
        'description': None,
        'schedule': '0 6 * * *',
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })

def test_list_tasks(app):
    test_client = app.test_client()

    response = json_call(test_client.get, '/tasks')
    assert response.status_code == 200
    assert response.json['count'] == 4
    assert response.json['page'] == 1
    assert response.json['total_pages'] == 1
    assert len(response.json['data']) == 4
    assert dict_contains(response.json['data'][0], {
        'name': 'task1',
        'workflow_name': 'workflow1',
        'active': True,
        'title': None,
        'description': None,
        'schedule': None,
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })
    assert dict_contains(response.json['data'][1], {
        'name': 'task2',
        'workflow_name': 'workflow1',
        'active': True,
        'title': None,
        'description': None,
        'schedule': None,
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })
    assert dict_contains(response.json['data'][2], {
        'name': 'task3',
        'workflow_name': 'workflow1',
        'active': True,
        'title': None,
        'description': None,
        'schedule': None,
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })
    assert dict_contains(response.json['data'][3], {
        'name': 'task4',
        'workflow_name': 'workflow1',
        'active': True,
        'title': None,
        'description': None,
        'schedule': None,
        'start_date': None,
        'end_date': None,
        'concurrency': 1,
        'sla': None,
        'default_priority': 'normal'
    })

def test_create_workflow_instance(app, instances):
    test_client = app.test_client()

    workflow_instance = {
        'workflow_name': 'workflow2',
        'unique': 'user-32324-payment-973794'
    }

    response = json_call(test_client.post, '/workflow-instances', workflow_instance)
    assert response.status_code == 201
    assert dict_contains(response.json, {
        'id': 2,
        'workflow_name': 'workflow2',
        'status': 'queued',
        'run_at': iso_regex,
        'unique': 'user-32324-payment-973794',
        'params': None,
        'priority': 'normal',
        'started_at': None,
        'scheduled': False,
        'ended_at': None,
        'created_at': iso_regex,
        'updated_at': iso_regex
    })

def test_get_workflow_instance(app, instances):
    test_client = app.test_client()

    response = json_call(test_client.get, '/workflow-instances/1')
    assert response.status_code == 200
    assert dict_contains(response.json, {
        'id': 1,
        'workflow_name': 'workflow1',
        'status': 'running',
        'run_at': '2017-06-03T06:00:00+00:00',
        'unique': None,
        'params': None,
        'priority': 'normal',
        'started_at': '2017-06-03T06:00:00+00:00',
        'scheduled': True,
        'ended_at': None,
        'created_at': iso_regex,
        'updated_at': iso_regex
    })

def test_list_workflow_instances(app, instances):
    test_client = app.test_client()

    response = json_call(test_client.get, '/workflow-instances')
    assert response.status_code == 200
    assert response.json['count'] == 1
    assert response.json['page'] == 1
    assert response.json['total_pages'] == 1
    assert len(response.json['data']) == 1
    assert dict_contains(response.json['data'][0], {
        'id': 1,
        'workflow_name': 'workflow1',
        'status': 'running',
        'run_at': '2017-06-03T06:00:00+00:00',
        'unique': None,
        'params': None,
        'priority': 'normal',
        'started_at': '2017-06-03T06:00:00+00:00',
        'scheduled': True,
        'ended_at': None,
        'created_at': iso_regex,
        'updated_at': iso_regex
    })

def test_update_workflow_instance(app, instances):
    test_client = app.test_client()

    response = json_call(test_client.get, '/workflow-instances/1')
    assert response.status_code == 200

    workflow_instance = response.json
    workflow_instance['priority'] = 'high'
    previous_updated_at = response.json['updated_at']

    response = json_call(test_client.put, '/workflow-instances/1', workflow_instance)
    assert response.status_code == 200
    assert dict_contains(response.json, {
        'id': 1,
        'workflow_name': 'workflow1',
        'status': 'running',
        'run_at': iso_regex,
        'unique': None,
        'params': None,
        'priority': 'high',
        'started_at': iso_regex,
        'scheduled': True,
        'ended_at': None,
        'created_at': iso_regex,
        'updated_at': iso_regex
    })
    assert response.json['updated_at'] > previous_updated_at

def test_delete_workflow_instance(app, instances):
    test_client = app.test_client()

    response = json_call(test_client.get, '/workflow-instances/1')
    assert response.status_code == 200

    response = json_call(test_client.get, '/task-instances?workflow_instance_id=1')
    assert response.status_code == 200
    assert response.json['count'] == 4

    response = json_call(test_client.delete, '/workflow-instances/1')
    assert response.status_code == 204

    response = json_call(test_client.get, '/workflow-instances/1')
    assert response.status_code == 404

    response = json_call(test_client.get, '/task-instances?workflow_instance_id=1')
    assert response.status_code == 200
    assert response.json['count'] == 0
