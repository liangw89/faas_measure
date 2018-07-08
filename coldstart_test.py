from utils import *


def coldstart_measure(
        rd_id,
        runtime,
        mem_size,
        thread_no,
        sleep_tm,
        wait_tm,
        log_file="tmp.log"):
    """
    Args:
        rd_id: an ID for this round of measurement
        runtime: "python2.7", "python3.6", "nodejs6.10", or "nodejs4.3"
        mem_size: the memory of the function
        thread_no: the number of workers (threads) initialized.
        sleep_tm: the function will start tasks after current time + sleep_tm;
        check code/python/index.py
        wait_tm: sleep for wait_tm before return
        log_file: the file for logging results 

    """
    func_prex = "coldstart"
    aws_id, aws_key, region, roles = get_config_basic()
    role = roles[0]
    zipped_code_path = os.path.join(os.getcwd(), "tmp.zip")
    func_handler = "index.handler"

    def worker_func(fop, **args):
        para = get_default_req(sleep_tm)
        res = fop.send_one_request(para)
        return res

    exp = Worker(log_file, rd_id, thread_no, worker_func)
    exp.init()

    para_list = []
    src_code_path = os.path.join(os.getcwd(), CODE_PATH[runtime])
    zip_code(zipped_code_path, src_code_path)

    fops = []
    for i in xrange(thread_no):
        func_name = func_prex + str(int(time.time() * 1000))[-8:]
        fop = FuncOp(
            aws_id,
            aws_key,
            region,
            role,
            runtime,
            mem_size,
            func_name)
        fop.del_function()
        fop.create_function(zipped_code_path, func_handler)
        para = (fop,)
        para_list.append(para)
        fops.append(fop)

    exp.add_tasks(para_list)        # measuring coldstart latency
    exp.clear_queue()
    exp.add_tasks(para_list)        # measuring warmstart latency
    exp.clear_queue()

    for fop in fops:
        fop.del_function()

    time.sleep(wait_tm)


def main():
    runtime_list = ['python2.7', 'nodejs4.3']
    mem_list = [128, 3008]
    rd_id = 1
    log_file = "tmp.log"
    clear_log = True
    thread_no = 2
    sleep_tm = 0
    wait_tm = 0

    open(log_file, "w")         # clear log file
    for rd_id in xrange(2):
        for runtime in runtime_list:
            for mem_size in mem_list:
                coldstart_measure(
                    rd_id,
                    runtime,
                    mem_size,
                    thread_no,
                    sleep_tm,
                    wait_tm,
                    log_file)


if __name__ == '__main__':
    main()
