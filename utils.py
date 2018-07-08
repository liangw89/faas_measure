import boto3
import datetime
import json
from zipfile import ZipFile
from collections import OrderedDict
import uuid
import time
from urlparse import urlparse
from threading import Thread
import httplib
from Queue import Queue
import uuid
import boto3
import json

import random
import os
import sys
import copy
import decimal


from conf import *


def fstr(f):
    """
    Convert a float number to string
    """
    ctx = decimal.Context()
    ctx.prec = 20
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')


def run_cmd(cmd):
    """
    The simplest way to run an external command
    """
    return os.popen(cmd).read()


def zip_code(zip_name, code_path):
    """
    Zip the source function files to a deployment package
    """
    with ZipFile(zip_name, 'w') as lambda_zip:
        if not os.path.isdir(code_path):
            lambda_zip.write(code_path)
        else:
            for root, dirs, fs in os.walk(code_path):
                for f in fs:
                    abs_path = os.path.join(root, f)
                    lambda_zip.write(abs_path, f)


def get_config_basic():
    """
    Get the credentials and basic setting from the config file
    """
    aws_id = CONGIF["creds"]["aws_id"]
    aws_key = CONGIF["creds"]["aws_key"]
    region = CONGIF["func"]["region"]
    roles = [CONGIF["func"]["role_1"], CONGIF["func"]["role_2"]]

    return aws_id, aws_key, region, roles


def get_default_req(sleep_tm):
    """
    Construct the basic request
    By default all the parameters in the request are set to False to skip
    the tests, except sleep_tm and stat

    Args:
            sleep_tm: the function start tasks after 
            current time + sleep_tm 
            
    """
    d = copy.deepcopy(PARA_TEMP)
    for k in d:
        d[k] = False
    d["stat"] = dict(argv=1)
    d["sleep"] = (time.time() + sleep_tm) * 1000
    return {"cmds": d}


def append_io_req(req, rd, size, cnt):
    """
    Construct a request for the IO throughput test
    Args:
            req: the basic request
            rd: no. of rounds
            size: the size of data to write each time
            cnt: the times to write in each round
    Example:
            append_io_req(rd=5, size=1kB, cnt=1000)
            write 1kB 1000 times using dd, repeat 5 rounds
    """

    req["cmds"]["io"] = dict(rd=rd, size=size, cnt=cnt)
    return req


def append_net_req(req, server_ip, port):
    """
    Construct a request for the network throughput test
    By default the port number starts from 5000

    Args:
            req: the basic request
            port_offset: the offset of the port number;
            server_ip: the IP of the iperf server
    Example:
            append_net_req(port_offset=5, server_ip="1.1.1.1")
            run network throughput tests using iperf with 
            server at 1.1.1.1:5005
    """
    req["cmds"]["net"] = dict(port=port, server_ip=server_ip)
    return req


def append_cpu_req(req, n):
    """
    Construct a request for the CPU test
    Args:
            req: the basic request
            n: the CPU test will calculate n! and record the time
    """
    req["cmds"]["cpu"] = dict(n=n)
    return req


def append_cpuu_req(req, n):
    """
    Construct a request for the CPU utilization test
    Args:
            req: the basic request
            n: the CPU utilization test will record n timestamps
    """
    req["cmds"]["cpuu"] = dict(n=n)
    return req

# if runtime not in ['java8']:
# 	zip_file_name = '%s_lambda.zip' % func_name
# 	with ZipFile(zip_file_name, 'w') as lambda_zip:
# 		lambda_zip.write(src_file)

# 	_handler = '%s.handler' % src_file.split(".")[0]

# else:
# 	cmd = "gradle build"
# 	run_cmd(cmd)
# 	zip_file_name = "build/distributions/code.zip"
# 	_handler = "example.Target::handleRequest"


class FuncOp():
    """
    The class for function operation

    """

    def __init__(
            self,
            aws_id,
            aws_key,
            region,
            role,
            runtime,
            memory,
            func_name):
        self.aws_id = aws_id
        self.aws_key = aws_key
        self.region = region
        self.role = role
        self.runtime = runtime
        self.memory = memory
        self.func_name = func_name

    def get_func_name(self):
        return self.func_name

    def set_func_role(self, role):
        self.role = role

    def set_func_runtime(self, runtime):
        self.runtime = runtime

    def set_func_memory(self, memory):
        self.memory = memory

    def set_func_name(self, name):
        self.func_name = name


    def get_client(self):
        """
        run this everytime to get a new connection
        should not use a persistent connection
        """
        session = boto3.Session(aws_access_key_id=self.aws_id,
                                aws_secret_access_key=self.aws_key,
                                region_name=self.region)
        client = session.client(service_name='lambda')
        return client

    def del_function(self):
        try:
            client = self.get_client()
            client.delete_function(FunctionName=self.func_name)
            return True
        except Exception as e:
            # print str(e)
            return False

    def create_function(self, src_file, func_handler):
        """
        Create a new function

        Args:
                src_file: the DIRECTORY for the code
                all the files under the directory will be zipped
                func_handler: the name of the function entry point
        """
        try:
            client = self.get_client()
            with open(src_file) as zip_blob:
                response = client.create_function(
                    Code={'ZipFile': zip_blob.read()},
                    Description='',
                    FunctionName=self.func_name,
                    Handler=func_handler,
                    MemorySize=self.memory,
                    Publish=True,
                    Role=self.role,
                    Runtime=self.runtime,
                    Timeout=300,
                )
            return True
        except Exception as e:
            print str(e)
            return False

    def update_function(self, key, value):
        assert key in ["role", "memory", "env"]
        client = self.get_client()
        if key == "role":
            client.update_function_configuration(
                FunctionName=self.func_name, Role=value)
        elif key == "memory":
            client.update_function_configuration(
                FunctionName=self.func_name, MemorySize=value)
        elif key == "env":
            client.update_function_configuration(
                FunctionName=self.func_name, Environment=value)
        return True

    def dump_meta(self):
        """
        The basic information to record
        """
        return "{}#{}#{}#{}".format(
            self.region,
            self.runtime,
            self.memory,
            self.func_name)

    def send_one_request(self, req_para={}):
        client = self.get_client()
        tm_st = time.time() * 1000
        resp = client.invoke(
            FunctionName=self.func_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(req_para)
        )
        tm_ed = time.time() * 1000
        try:
            resp = json.loads(resp['Payload'].read())
        except Exception as e:
            print str(e), resp
        if not resp:
            resp = "ERROR"
        out = "{}#{}#{}#{}".format(
            resp, fstr(tm_st), fstr(tm_ed), fstr(
                tm_ed - tm_st))
        out = "{}#{}".format(self.dump_meta(), out)
        return out


class Worker():
    """
    A queue-based multiple threading framework for sending
    parallel requests
    """

    def __init__(self, fout, rd_id, work_no, func):
        self.fout = fout
        self.work_no = work_no
        self.rd_id = rd_id
        self.func = func
        self.subrd_id = 0
        self.q = Queue(10000)
        self.task_no = 0

    def set_rdid(self, _id):
        self.rd_id = _id

    def set_subrdid(self, _id):
        self.subrd_id = _id

    def clear_queue(self):
        with self.q.mutex:
            self.q.queue.clear()

    def run_task(self, task):
        while True:
            work_id, para = self.q.get()

            res = task(para)
            _entry = "{}#{}#{}#{}#{}\n".format(
                self.rd_id, self.subrd_id, self.task_no, work_id, res)
            open(self.fout, "a").write(_entry)
            # print res
            self.q.task_done()

    def init(self):
        for i in range(self.work_no):
            t = Thread(target=self.run_task, args=(self.task,))
            t.daemon = True
            t.start()

    def add_tasks(self, para_list):
        self.task_no = len(para_list)
        self.subrd_id += 1
        try:
            for i in xrange(self.task_no):
                para = para_list[i]
                work_id = i
                self.q.put((work_id, para))
            self.q.join()
        except KeyboardInterrupt:
            sys.exit(1)

    def task(self, para):
        """
        Customized your task here
        """
        res = self.func(*para)
        return res
