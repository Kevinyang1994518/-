#!/bin/python3

#解析output下的日志，生成json格式的web请求

import os
import sys
import requests
import json
import re
import time
import traceback
from datetime import datetime

logpath='/home/uos'
if len(sys.argv) > 1:
    logpath = sys.argv[1]

if not os.path.exists(logpath):
    print("log目录不存在")
    exit()

#机型
def parse_machine():
    vendor = '<Manufacturer>'
    product= '<Product Name>'
    chassis= '<Chassis Type>'
    with open(os.path.join(logpath,"hwinfo/dmi.info"), 'r') as f:
        fstr = f.read()
    paraphs = fstr.split('\n\n')[:-1] #dmi.info以\n\n结尾，会多出一个空串作为最后一段，需要删去
    for p in paraphs:
        plines = p.split('\n')
        if plines[1] == 'System Information':
            for line in plines:
                pair = line.split(": ")
                if pair[0] == '\tManufacturer':
                    vendor = pair[1]
                elif pair[0] == '\tProduct Name':
                    product = pair[1]
                elif pair[0] == '\tSKU Number':
                    product += "({})".format(pair[1])
                else:
                    pass
        elif plines[1] == 'Chassis Information':
            for line in plines:
                pair = line.split(": ")
                if pair[0] == '\tType':
                    chassis = pair[1]
        else:
            pass
    return vendor, product, chassis

#CPU信息
def parse_cpu():
    cpu_model_name = '<Model name>'
    cpus = '1'
    with open(os.path.join(logpath,"hwinfo/cpu.info"), 'r') as f:
        lines = f.read().splitlines()
    for line in lines:
        pair = line.split(':')
        if pair[0] == 'Model name':
            cpu_model_name = pair[1].strip()
        if pair[0] == 'CPU(s)':
            cpus  = pair[1].strip()
    return cpu_model_name, cpus

#提交号
def parse_commit():
    commit_id = 'unknown'
    with open(os.path.join(logpath,"hwinfo/kernel.log"), 'r') as f:
        banner = f.readline().strip('\n')
    pattern = re.compile('\([0-9A-Fa-f]+\)')
    try:
        commit_id = re.findall(pattern, banner)[-1].strip('()') # short commit-id from 1st line of dmesg
    except IndexError:
        commit_id = "未在内核日志中找到commit-id"
    return commit_id

#测试项目
def parse_hw_cpuoffon(corenum):
    result = 'unknown'
    info = ''
    try:
        with open(os.path.join(logpath,"cpu.log"), 'r') as f:
            cpulog = f.read()
        cpulog = cpulog.split('\n\n')[:-1]
        assert len(cpulog) == corenum - 1 # boot core will not offline
        
        coretable = [[0,0] for i in range(corenum)] #[ [x,x], [off_y,on_y], [], [], [], ...]
        pat_on  = re.compile('cpu \[.*\] has been online')
        pat_off = re.compile('cpu \[.*\] has been offline')
        pat_core= re.compile('\[.*?\]')
        for corelog in cpulog:
            matchlist = re.findall(pat_off, corelog)
            if len(matchlist) == 0:
                continue
            off_str = matchlist[0]
            corei = int(re.findall(pat_core, off_str)[0][1:-1])
            coretable[corei][0] = 1

            matchlist = re.findall(pat_on, corelog)
            if len(matchlist) == 0:
                continue
            on_str = matchlist[0]
            corei = int(re.findall(pat_core, on_str)[0][1:-1])
            coretable[corei][1] = 1
        for i in range(1, corenum):
            if coretable[i][0] == 0:
                info  += 'core [{}] offline failed\n'.format(i)
                result = 'fail'
            if coretable[i][1] == 0:
                info  += 'core [{}] online failed\n'.format(i)
                result = 'fail'
        result = 'pass'
    except IOError:
        print("cpu.log日志解析异常")
        result = 'fail'
    except AssertionError:
        print("CPU核心数不匹配")
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        print(traceback.format_exc())
    finally:
        return result, info

def parse_hw_cpufreq(corenum):
    result = 'unknown'
    info = ''
    
    try:
        with open(os.path.join(logpath,"cpufreq.log"), 'r') as f:
            freqlog = f.read()
        freqlog = freqlog.split('\n\n')[:-1]
        assert len(freqlog) == 2
        result = 'pass'

        d = dict({
            "schedutil"   : ['\x1b[31mCONFIG_CPU_FREQ_GOV_SCHEDUTIL   \t\t\t\t   y\x1b[0m', '\x1b[31mCONFIG_CPU_FREQ_GOV_SCHEDUTIL   \t\t\t\t   m\x1b[0m'],
            "conservative": ['\x1b[31mCONFIG_CPU_FREQ_GOV_CONSERVATIVE\t\t\t\t   y\x1b[0m', '\x1b[31mCONFIG_CPU_FREQ_GOV_CONSERVATIVE\t\t\t\t   m\x1b[0m'],
            "ondemand"    : ['\x1b[31mCONFIG_CPU_FREQ_GOV_ONDEMAND    \t\t\t\t   y\x1b[0m', '\x1b[31mCONFIG_CPU_FREQ_GOV_ONDEMAND    \t\t\t\t   m\x1b[0m'],
            "userspace"   : ['\x1b[31mCONFIG_CPU_FREQ_GOV_USERSPACE   \t\t\t\t   y\x1b[0m', '\x1b[31mCONFIG_CPU_FREQ_GOV_USERSPACE   \t\t\t\t   m\x1b[0m'],
            "powersave"   : ['\x1b[31mCONFIG_CPU_FREQ_GOV_POWERSAVE   \t\t\t\t   y\x1b[0m', '\x1b[31mCONFIG_CPU_FREQ_GOV_POWERSAVE   \t\t\t\t   m\x1b[0m'],
            "performance" : ['\x1b[31mCONFIG_CPU_FREQ_GOV_PERFORMANCE \t\t\t\t   y\x1b[0m', '\x1b[31mCONFIG_CPU_FREQ_GOV_PERFORMANCE \t\t\t\t   m\x1b[0m']
        })
        cfg_support_list = []
        cfgchk = freqlog[0].split('\n')
        syschk = freqlog[1].split('\n')
        for k,v in d.items():
            # if v in cfgchk:
            if True in [v[i] in cfgchk for i in range(len(v))]:
                cfg_support_list.append(k)
        #print(support_list) #取得内核配置显示支持的 cpufreq governor
        cfg_support_list.sort()
        sorted_support_str = ' '.join(cfg_support_list)
        info += "config支持的governor: {}\n".format(sorted_support_str)

        coretable = list(range(corenum)) #[ 0, 1, 2, 3, ..., corenum -1 ]
        corevisit = [0 for i in range(corenum)]
        pattern = re.compile('\[.*?\]') #提取中括号及其内容, '?'进行贪婪匹配
        for line in syschk:
            matchlist = re.findall(pattern, line)
            if len(matchlist) != 2:
                continue
            corei            = int(matchlist[0][1:-1])
            corevisit[corei] = 1
            sys_support_list = matchlist[1][1:-1].strip().split()
            sys_support_list.sort()
            if sorted_support_str != ' '.join(sys_support_list):
                coretable[corei] = -1
        for i in coretable:
            if i == -1:
                result = 'fail'
                info += 'cpufreq: governor of core[{}] do not match kernel config\n'.format(i)
        for i in range(corenum):
            if corevisit[i] == 0:
                result = 'fail'
                info += 'cpufreq: core[{}] have no sysfs info\n'.format(i)
    except IOError:
        print("cpufreq.log日志解析异常")
        result = 'fail'
        info = 'log not found\n'
    except AssertionError:
        info = '2个阶段不完整'
    except:
        print('Unexpected Error', sys.exc_info())
        print(traceback.format_exc())
    finally:
        return result, info

def parse_stable_s3():
    result   = 'unknown'
    timespan = 'unknown'
    try:
        with open(os.path.join(logpath,"S3.log"), 'r') as f:
            s3log = f.read().splitlines()
        assert s3log != []
        if s3log[-1][:6] == '完成待机测试':
            result   = "pass"
            for i in s3log:
                if i[-8:] == '第1次测试。。。':
                    s3start = time.strptime(i.split()[0], '%Y%m%d_%H-%M-%S')
                    break
            s3finish = time.strptime(s3log[-2].split()[0], '%Y%m%d_%H-%M-%S')
            hour = (time.mktime(s3finish) - time.mktime(s3start)) / 3600
            timespan = "用时{:.2f}小时".format(hour)
        else:
            result = 'fail'
    except IOError:
        print('S3日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except AssertionError:
        print('S3日志内容为空!')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        print(traceback.format_exc())
    finally:
        return result, timespan

def parse_stable_s4():
    result   = 'unknown'
    timespan = 'unknown'
    try:
        with open(os.path.join(logpath,"S4.log"), 'r') as f:
            s4log = f.read().splitlines()
        assert s4log != []
        if s4log[-1][:6] == '完成休眠测试':
            result   = "pass"
            for i in s4log:
                if i[-8:] == '第1次测试。。。':
                    s4start = time.strptime(i.split()[0], '%Y%m%d_%H-%M-%S')
                    break
            s4finish = time.strptime(s4log[-2].split()[0], '%Y%m%d_%H-%M-%S')
            hour = (time.mktime(s4finish) - time.mktime(s4start)) / 3600
            timespan = "用时{:.2f}小时".format(hour)
        else:
            result = 'fail'
    except IOError:
        print('S4日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except AssertionError:
        print('S3日志内容为空!')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
    finally:
        return result, timespan

def parse_stable_s5():
    result   = 'unknown'
    timespan = 'unknown'
    try:
        with open(os.path.join(logpath,"reboot.log"), 'r') as f:
            s5log = f.read().splitlines()
        if s5log[-1] == '重启测试已经完成':
            result   = "pass"
            s5start  = time.strptime(s5log[2].split()[0],'%Y%m%d_%H-%M-%S')
            s5finish = time.strptime(s5log[-3].split()[0],'%Y%m%d_%H-%M-%S')
            hour = (time.mktime(s5finish) - time.mktime(s5start)) / 3600
            timespan = "用时{:.2f}小时".format(hour)
        else:
            result = 'fail'
    except IOError:
        print('S5日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        raise
    finally:
        return result, timespan

def parse_memtest():
    result = 'unknown'
    try:
        with open(os.path.join(logpath,"memtest.log"), 'r') as f:
            log = f.read().splitlines()
        if log[-2] == 'Status: PASS - please verify no corrected errors':
            result   = "pass"
        else:
            result = 'fail'
    except IOError:
        print('memtest.log日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        print(traceback.format_exc())
    finally:
        return result

def parse_ltptest():
    result = 'unknown'
    try:
        with open(os.path.join(logpath,"ltp.log"), 'r') as f:
            log = f.read().splitlines()
        if log[-2] == 'Hostname: uos-PC':
            result   = "pass"
        else:
            result = 'fail'
    except IOError:
        print('ltp.log日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        print(traceback.format_exc())
    finally:
        return result

def parse_nettest():
    result = 'unknown'
    try:
        with open(os.path.join(logpath,"nettest/networktest.txt"), 'r') as f:
            log = f.read().splitlines()
        if log[-1] == 'All Tests Passed':
            result   = "pass"
        else:
            result = 'fail'
    except IOError:
        print('networktest.txt日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        print(traceback.format_exc())
    finally:
        return result

def parse_audio():
    result = 'pass'
    try:
        with open(os.path.join(logpath,"audio.log"), 'r') as f:
            log = f.read().splitlines()
        for i in range(1,len(log)):
            if log[i].split()[-1] == 'fail':
                result = 'fail'
                break
    except IOError:
        print('audio.log日志解析时IO异常!(找不到日志)')
        result = 'fail'
    except:
        print('Unexpected Error', sys.exc_info())
        result = 'unknown'
        print(traceback.format_exc())
    finally:
        return result

if __name__ == '__main__':
    ###-------------构建信息、硬件参数-------------###
    v, p, c = parse_machine()
    machine = v+' '+p+' '+c
    print("machine  : ", machine)
    cpumodel, cpucorenum = parse_cpu()
    cpumodel = cpumodel + " ({}-core)".format(cpucorenum)
    cpucorenum = int(cpucorenum)

    print("cpu      : ", cpumodel)
    print("commit-id: ", parse_commit())

    ###-----------------测试结果-----------------###
    print("cpu-offon: ", parse_hw_cpuoffon(cpucorenum))
    print("cpu-freq : ", parse_hw_cpufreq(cpucorenum))

    s3state, s3time = parse_stable_s3()
    print("stable-s3: ", s3state, s3time)

    s4state, s4time = parse_stable_s4()
    print("stable-s4: ", s4state, s4time)

    s5state, s5time = parse_stable_s5()
    print("stable-s5: ", s5state, s5time)

    print("memtest  : ", parse_memtest())
    print("ltptest  : ", parse_ltptest())

    ###---------------驱动功能测试---------------###
    print("nettest  : ", parse_nettest())
    print("audio    : ", parse_audio())

    ###--------------日志上传服务器--------------###
    today = datetime.now().strftime("%Y-%m-%d")
    host = os.popen("ifconfig | grep inet | grep -v inet6 | grep -v 127.0.0.1 | awk '{print $2}'").read()
    os.system('sshpass -p 1 ssh common@10.20.64.58 "mkdir -p ~/daily.log/{}/{}"'.format(today, host))
    os.system('sshpass -p 1 scp {}/* common@10.20.64.58:~/daily.log/{}/{}'.format(logpath, today, host))

    ###---------------解析日志结果---------------###
    jsonlist = {
        '内核_功能稳定性测试_机型'           :machine,
        '内核_功能稳定性测试_CPU'           :cpumodel,
        '内核_功能稳定性测试_COMMIT ID'     :parse_commit(),
        '内核_功能稳定性测试_CPU测试'        :parse_hw_cpuoffon(cpucorenum)[0],
        '内核_功能稳定性测试_DDR测试'        :parse_memtest(),
        '内核_功能稳定性测试_重启测试'       :s5state + ','+s5time,
        '内核_功能稳定性测试_待机唤醒测试'    :s3state +','+s3time,
        '内核_功能稳定性测试_休眠唤醒测试'    :s4state +','+s4time,
        '内核_功能稳定性测试_LTP压力测试'    :parse_ltptest(),
        # '内核_功能稳定性测试_BRANCH'        :'todo',
        '内核_功能稳定性测试_BIOS信息检查'   :'pass',
        # '内核_功能稳定性测试_磁盘测试'       :'todo',
        # '内核_功能稳定性测试_显卡测试'       :'todo',
        '内核_功能稳定性测试_网卡测试'       :parse_nettest(),
        '内核_功能稳定性测试_声卡测试'        :parse_audio(),
        # '内核_功能稳定性测试_USB、PCI设备测试' :'todo',
        # '内核_功能稳定性测试_其他设备（TRC、FP、LP）测试' :'todo',
        '内核_功能稳定性测试_描述'            :'',
        '内核_功能稳定性测试_附件'            :'common@10.20.64.58:~/daily.log/{}/{}/*'.format(today, host)
    }
    jsonstr = json.dumps(jsonlist, ensure_ascii=False)
    with open("./parsed.json", "w") as f:
        f.write(jsonstr)
    os.system('jq . --tab parsed.json')
    hookurl = 'https://cooperation.uniontech.com/api/workflow/hooks/NjQwZTdlYjU4MGVjYzkzZjhmOWMwOGU1'
    #res = requests.post(hookurl, data=jsonlist)
    # print(res.text)
    
