from utils import *

# the IPs of the perf servers for network tests
PERF_SERVER_IPS = ["1.1.1.1", "2.2.2.2"]

def perf_test(
        rd_id,
        runtime,
        mem_size,
        thread_no,
        sleep_tm,
        wait_tm,
        log_file="tmp.log"):
    func_prex = "perf_test"
    aws_id, aws_key, region, roles = get_config_basic()
    role = roles[0]
    zipped_code_path = os.path.join(os.getcwd(), "tmp.zip")
    func_handler = "index.handler"

    def worker_func(fop, i, **args):
        """
        Examples of constructing  requests for different tests;
        Uncomment the corresponding line to run the test
        """
        para = get_default_req(sleep_tm)


        para = append_cpuu_req(para, 1000)

        # para = append_cpu_req(para, 1000)

        # para = append_io_req(para, 3, "1kB", 10)
        
        # If you run multiple perf servers on the same IP with different ports
        # para = append_net_req(para, "34.227.13.37", 5000 + i + 1)
        # If you have set up perf servers on different IPs
        # para = append_net_req(para, PERF_SERVER_IPS[i], 5000)

        res = fop.send_one_request(para)
        return res

    def basic_probe_func(fop, **args):
        para = get_default_req(0)
        res = fop.send_one_request(para)
        return res

    def get_n_coresidency(mem_size, runtime, min_no):
        """
        Keep creating / deleting functions until finding
        min_no of instances on the same VM
        Return the operators for the coresident functions
        """
        fout = "tmp_coresidency.log"
        open(fout, "w")
        N = 10
        exp = Worker(fout, 0, N, basic_probe_func)
        exp.init()

        para_list = []
        src_code_path = os.path.join(os.getcwd(), CODE_PATH[runtime])
        zip_code(zipped_code_path, src_code_path)

        fops = []
        for i in xrange(N):
            func_name = func_prex + str(int(time.time() * 1000))[-8:]
            fop = FuncOp(
                aws_id,
                aws_key,
                region,
                role,
                runtime,
                mem_size,
                func_name)
            # fop.del_function()
            fop.create_function(zipped_code_path, func_handler)
            para = (fop, )
            para_list.append(para)
            fops.append(fop)

        exp.add_tasks(para_list)
        exp.clear_queue()

        buf = [v.strip("\n") for v in open(fout).readlines()]

        count = {}
        for v in buf:
            vm_id = v.split("#")[10]
            func_name = v.split("#")[7]
            if vm_id not in count:
                count[vm_id] = []
            count[vm_id].append(func_name)
        key_max = max(count, key=lambda k: len(count[k]))
        # print count

        # print count[key_max], len(count[key_max])

        if len(count[key_max]) >= min_no:
            target_ops = [
                v for v in fops if v.get_func_name() in count[key_max]]
            return target_ops
        else:
            for fop in fops:
                fop.del_function()

    exp = Worker(log_file, rd_id, thread_no, worker_func)
    exp.init()

    fops = get_n_coresidency(mem_size, runtime, thread_no)

    para_list = []

    for i in xrange(thread_no):
        fop = fops[i]
        para = (fop, i)
        para_list.append(para)
        fops.append(fop)

    exp.add_tasks(para_list)
    exp.clear_queue()

    for fop in fops:
        fop.del_function()

    time.sleep(wait_tm)


def main():
    runtime_list = ['python2.7']
    mem_list = [128]
    rd_id = 2
    log_file = "tmp.log"
    thread_no = 3
    sleep_tm = 0
    wait_tm = 0
    open(log_file, "w")
    for runtime in runtime_list:
        for mem_size in mem_list:
            perf_test(
                rd_id,
                runtime,
                mem_size,
                thread_no,
                sleep_tm,
                wait_tm,
                log_file)


if __name__ == '__main__':
    main()
