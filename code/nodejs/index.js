
function run_cmd(cmd) {

    var exec = require('child_process').execSync;
    var res = exec(cmd);
    var out = res.toString().replace(/[\n\t\r]/g, '');
    return out;
}


function get_ip() {
    var cmd = "curl -s 'http://checkip.dyndns.org'";
    var tmp = run_cmd(cmd).toString().split(":");
    tmp = tmp[1];
    tmp = tmp.split("<");
    res = tmp[0].replace(/\s/g, '');
    return res;
}



function run_tests(req, context){

    var out;
    var fs = require('fs');
    var buf =  fs.readFileSync('/proc/self/cgroup', 'utf8').toString()
    buf = buf.split("\n");
    buf = buf[buf.length - 3];
    buf = buf.split("/");
    var r_id = buf[1];
    var c_id = buf[2];
    
    var tmp = run_cmd("cat /proc/uptime");
    var uptime = tmp.toString().replace(/[\n\t\r]/g, '');

    var vm_pub_ip = get_ip();
    
    var vm_priv_ip = run_cmd("uname -n").toString().replace(/[\n\t\r]/g, '');
    vm_priv_ip = vm_priv_ip.replace('ip-', '');
    vm_priv_ip = vm_priv_ip.replace(/\-/g, '.');
    

    var new_id = makeid();

    var exist_id;

    var fname = "/tmp/test_access.log";

    if (fs.existsSync(fname) != true){
        fs.writeFileSync(fname, new_id);
        exist_id = new_id;
    }
    else{
        exist_id = fs.readFileSync(fname, 'utf8').toString();
    }

    out = r_id + "#" + c_id + "#" + exist_id + "#" + new_id;
    
    out = out + "#" + vm_pub_ip + "#" + vm_priv_ip + "#" + "unknown";
    
    out = out + "#" + uptime;

    return out;
}



exports.handler = (event, context, callback) => {
    // Example input: {"eid":1, "memtest":0}
    var start = new Date().getTime();
    var sleep_tm = event.cmds.sleep;

    var wait_util = sleep_tm; 
    while (new Date().getTime() < wait_util){}

    
    var tmp = run_cmd("python stats.py stat_basic")

    var end = new Date().getTime();
    var out = tmp + "#" + start + "#" + end + "#" + (end - start);
    callback(null, out);

};

////////////////////////////////////