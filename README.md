# Taskflow

## Overview

An advanced yet simple system to run your background tasks and workflows.

Features

- Recurring tasks (aka jobs) and workflows (a series of dependent tasks) with CRON-like scheduling


- Workflow dependencies - tasks execute in order and/or in parallel depending on dependency chain.

- Two types of workers that execute tasks
	- Pull workers - Pull tasks directly off the database queue and execute them.
	- Push workers - Tasks are pushed to a remote work management system, such as AWS Batch, Kubernetes, or Apache Mesos. Container friendly.

## Motivation

Other background task and workflow management solutions exist out there, such as Celery for tasks/jobs or Airflow and Luigi for workflows. Taskflow is designed to have a small footprint, maintain it's state in a readily queryable SQL database, have predictable CRON-like scheduling behavior, and GTFO of the way when you need it to.

## Concepts

### Task

A Task represents some runnable code or command. For example, extact a table from a database, or push to an API. Anything that can run in pyhon or be excuted in Bash.

### Task Instances

A Task Instance is a specific run of a Task. Task instances can be created programmatically on-demand or automatically using a recurring schedule attached to a Task.

#### Workflows

A Workflow represents a series of dependent tasks represent in a graph. Workflows are associated to the Tasks they run.

#### Workflow Instances

A Workflow Instance is a specific run of a Workflow. A Workflow Instance creates Task Instances as needed during a run. Like a Task Instance, Workflow Instances can be created programmatically on-demand or automatically using a recurring schedule attached to a Workflow.

#### Scheduler

The scheduler always runs as a single instance at a time. It schedules recurring Tasks and recurring Workflows. It also advances running Workflow Instances, scheduling Task Instances as needed.

#### Pusher

The Pusher is usually run within the same process as the scheduler. The Pusher pulls tasks destined for a push worker off the task_instances table and pushes them to the push destination. For examples, pushing tasks to AWS Batch. The Push also syncs the state of the currently pushed tasks with the push destination. Multiple push destinations can be used at the same time, for example one task could go to AWS Batch while another goes to Kubernetes.

#### Pull Worker

A pull worker is a process that directly pulls tasks off the queue and executes them.