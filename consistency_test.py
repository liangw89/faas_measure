from utils import *


def consistency_measure(
        rd_id,
        runtime,
        mem_size,
        thread_no,
        sleep_tm,
        wait_tm,
        log_file="tmp.log"):

    func_prex = "consistency"
    aws_id, aws_key, region, roles = get_config_basic()

    
    

    zipped_code_path = os.path.join(os.getcwd(), "tmp.zip")
    func_handler = "index.handler"

    role0 = roles[0]

    role1 = roles[1]

    def worker_func(fop, **args):
        para = get_default_req(sleep_tm)
        res = fop.send_one_request(para)

        res = res + "#" + str(fop.role)
        
        return res


    exp = Worker(log_file, rd_id, thread_no, worker_func)
    exp.init()


    para_list = []
    src_code_path = os.path.join(os.getcwd(), CODE_PATH[runtime])
    zip_code(zipped_code_path, src_code_path)

    fops = []

    func_name = func_prex + str(int(time.time() * 1000))[-8:]

    fop = FuncOp(
            aws_id,
            aws_key,
            region,
            role0,
            runtime,
            mem_size,
            func_name)
        
    fop.del_function()

    # open("code/python/index.py").write("#")   # update function code

    fop.create_function(zipped_code_path, func_handler)

    # send the first batch of requests
    exp.add_tasks([(fop,) for i in xrange(thread_no)])        
    exp.clear_queue()

    # wait for a few seconds and update the function

    time.sleep(wait_tm)

    fop.set_func_role(role1)
    fop.update_function("role", role1)

    
    # send the second batch of requests
    exp.add_tasks([(fop,) for i in xrange(thread_no)])      
    exp.clear_queue()

    fop.del_function()

    


def main():
    runtime = "python2.7"
    mem_size = 128
    rd_id = 1
    log_file = "tmp.log"

    thread_no = 5
    sleep_tm = 5
    wait_tm = 0

    open(log_file, "w")         # clear log file
    for rd_id in xrange(1):
        consistency_measure(
            rd_id,
            runtime,
            mem_size,
            thread_no,
            sleep_tm,
            wait_tm,
            log_file)


if __name__ == '__main__':
    main()
