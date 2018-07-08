from utils import *


def lifetime_test(N, runtime, mem_size, sleep_tm, wait_tm, log_file="tmp.log"):
    func_prex = "lifetime"
    aws_id, aws_key, region, roles = get_config_basic()
    role = roles[0]
    zipped_code_path = os.path.join(os.getcwd(), "tmp.zip")
    func_handler = "index.handler"

    def worker_func(fop, **args):

        para = get_default_req(sleep_tm)
        res = fop.send_one_request(para)
        return res

    rd_id = 0
    exp = Worker(log_file, rd_id, 1, worker_func)
    exp.init()

    func_name = func_prex + str(int(time.time() * 1000))[-8:]
    src_code_path = os.path.join(os.getcwd(), CODE_PATH[runtime])
    zip_code(zipped_code_path, src_code_path)
    fop = FuncOp(aws_id, aws_key, region, role, runtime, mem_size, func_name)
    fop.del_function()
    fop.create_function(zipped_code_path, func_handler)

    while rd_id < N:

        para_list = []

        para = (fop, )
        para_list.append(para)

        exp.add_tasks(para_list)
        exp.clear_queue()

        time.sleep(wait_tm)

        rd_id += 1
        exp.set_rdid(rd_id)
        exp.set_subrdid(0)

    fop.del_function()


def main():
    runtime = 'python2.7'
    mem_size = 128
    log_file = "tmp.log"
    sleep_tm = 0
    wait_tm = 0
    N = 5
    open(log_file, "w")
    lifetime_test(N, runtime, mem_size, sleep_tm, wait_tm, log_file)


if __name__ == '__main__':
    main()
