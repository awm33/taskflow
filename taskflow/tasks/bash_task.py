import os
import signal
import logging
import re
import sys
import shutil
from subprocess import Popen, PIPE
from tempfile import gettempdir, NamedTemporaryFile
from threading import Thread
from contextlib import contextmanager
from tempfile import mkdtemp

from smart_open import smart_open
import boto
import boto3

from taskflow import Task

s3_regex = r'^s3://([^/]+)/(.+)'

def fopen(file, mode='r'):
    # HACK: get boto working with instance credentials via boto3
    match = re.match(s3_regex, file)
    if match != None:
        client = boto3.client('s3')
        s3_connection = boto.connect_s3(
            aws_access_key_id=client._request_signer._credentials.access_key,
            aws_secret_access_key=client._request_signer._credentials.secret_key,
            security_token=client._request_signer._credentials.token)
        bucket = s3_connection.get_bucket(match.groups()[0])
        if mode == 'w':
            file = bucket.get_key(match.groups()[1], validate=False)
        else:
            file = bucket.get_key(match.groups()[1])
    return smart_open(file, mode=mode)

def pipe_stream(stream1, stream2):
    def stream_helper(stream1, stream2):
        for line in iter(stream1.readline, b''):
            stream2.write(line)
        stream2.close()

    t = Thread(target=stream_helper, args=(stream1, stream2))
    t.daemon = True
    t.start()

@contextmanager
def TemporaryDirectory(suffix='', prefix=None, dir=None):
    name = mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as e:
            # ENOENT - no such file or directory
            if e.errno != errno.ENOENT:
                raise e

class BashTask(Task):
    def get_command(self):
        return self.params['command']

    def execute(self, task_instance):
        logger = logging.getLogger(self.name)
        bash_command = self.get_command()
        logger.info('Temporary directory root location: %s', gettempdir())
        with TemporaryDirectory(prefix='taskflowtmp') as tmp_dir:
            with NamedTemporaryFile(dir=tmp_dir, prefix=str(task_instance.id)) as f:
                f.write(bytes(bash_command, 'utf_8'))
                f.flush()
                fname = f.name
                script_location = tmp_dir + "/" + fname
                logger.info('Temporary script location: %s', script_location)
                logger.info('Running command: %s', bash_command)

                input_file = None
                if 'input_file' in task_instance.params and task_instance.params['input_file'] != None:
                    input_file = fopen(task_instance.params['input_file'])
                elif 'input_file' in self.params and self.params['input_file'] != None:
                    input_file = fopen(self.params['input_file'])

                out = None
                if 'output_file' in task_instance.params and task_instance.params['output_file'] != None:
                    out = fopen(task_instance.params['output_file'], mode='w')
                elif 'output_file' in self.params and self.params['output_file'] != None:
                    out = fopen(self.params['output_file'], mode='w')

                ON_POSIX = 'posix' in sys.builtin_module_names

                sp = Popen(
                    ['bash', fname],
                    stdin=PIPE if input_file else None,
                    stdout=PIPE if out else None,
                    stderr=PIPE,
                    cwd=tmp_dir,
                    preexec_fn=os.setsid,
                    bufsize=1,
                    close_fds=ON_POSIX)

                self.sp = sp

                if input_file:
                    pipe_stream(input_file, sp.stdin)

                if out:
                    pipe_stream(sp.stdout, out)

                for line in iter(sp.stderr.readline, b''):
                    logger.info(line)

                sp.wait()

                if input_file:
                    input_file.read_key.close(fast=True)

                logger.info('Command exited with return code %s', sp.returncode)

                if sp.returncode:
                    raise Exception('Bash command failed')

    def on_kill(self):
        logging.info('Sending SIGTERM signal to bash process group')
        os.killpg(os.getpgid(self.sp.pid), signal.SIGTERM)