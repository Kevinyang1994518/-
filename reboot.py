#!/usr/bin python3
#*-*coding:utf-8
import time
import os
import sys



print(
    """
    #readme
    必须在 /home/uos 目录执行脚本
    sudo python3 reboot.py 重启次数
    """)



def run_reboot():
    
    print("trig: run_reboot")
    os.environ['DISPLAY'] = ':0'

    # 确保 apt update 时有网络，能获得锁
    print(os.popen('while ! ping -c 1 -w 2 uniontech.com;do echo 1 | sudo -S dhclient; echo 再次等待网络连接; sleep 2; done').read())
    os.system("while ps -ef | grep apt | grep -v grep >/dev/null;do echo 'wait for dpkg lock'; sleep 2; done")

    os.system("echo '1'|sudo -S apt update")
    os.system("echo 1 | sudo -S apt install python3-pip libjpeg-dev zlib1g-dev -y")
    all = os.popen("pip3 list").read()

    if "PyAutoGUI" in all:
        print("存在 PyAutoGUI 库")
    else:
        print("不存在 PyAutoGUI 库")
        os.system("pip3 install pyautogui -i https://pypi.douban.com/simple/")


    # 安装必要库
    print("安装必要库")
    os.system("echo 1 | sudo -S apt-get install python3-tk -y")
    listdir=os.listdir("/home/uos/")
    
    time.sleep(10)
    #不能将这个import移动到文件开头！！！
    import pyautogui
    pyautogui.FAILSAFE = True

    # 打开终端
    print("打开终端")
    pyautogui.hotkey("ctrl", "alt","t")
    time.sleep(5)
    # 输入内容
    pyautogui.typewrite(message="sudo su", interval="0.25")
    time.sleep(1)
    pyautogui.press("enter", interval=0.25)
    time.sleep(1)
    pyautogui.typewrite(message="1", interval="0.25")
    time.sleep(1)
    pyautogui.press("enter", interval=0.25)
    # 输入内容
    pyautogui.typewrite(message="bash wrietpath.sh", interval="0.25")
    time.sleep(1)
    pyautogui.press("enter", interval=0.25)
    time.sleep(20)



def write_path(count):
    pathmesg = '''#!/bin/bash
#设置自动登录并清空秘钥环
function set_autoLogin(){
    dbus-send --system --dest=com.deepin.daemon.Accounts --print-reply /com/deepin/daemon/Accounts/User1000 com.deepin.daemon.Accounts.User.EnableNoPasswdLogin boolean:true
    sleep 1
    dbus-send --system --dest=com.deepin.daemon.Accounts --print-reply /com/deepin/daemon/Accounts/User1000 com.deepin.daemon.Accounts.User.SetAutomaticLogin boolean:true
    sleep 1
    rm -f /home/uos/.local/share/keyrings/*
    sleep 1
}

#关闭自动登录
function off_autoLogin(){
    dbus-send --system --dest=com.deepin.daemon.Accounts --print-reply /com/deepin/daemon/Accounts/User1000 com.deepin.daemon.Accounts.User.EnableNoPasswdLogin boolean:false
    sleep 1
    dbus-send --system --dest=com.deepin.daemon.Accounts --print-reply /com/deepin/daemon/Accounts/User1000 com.deepin.daemon.Accounts.User.SetAutomaticLogin boolean:false
    sleep 1
}

# 自启动变量
TESTPATH=/home/uos
run_pwd=$TESTPATH/reboot.py
run_path=/lib/systemd/system/test.service

#自启服务
function reboot_server(){
    if [[ -x $run_path ]];then
        echo "存在自启动"
        # 重新加载配置文件
        systemctl daemon-reload
        systemctl enable test.service
    else
        cat > $run_path << EOF
[Unit]
Description=test
After=network.target
After=lightdm.service
[Service]
Type=simple
ExecStart=/usr/bin/python3 $run_pwd
User=uos
[Install]
WantedBy=graphical.target
EOF

    chmod 777 $run_path
    # 重新加载配置文件
    systemctl daemon-reload
    systemctl enable test.service

    #关闭主服务自启动
    systemctl disable daily.service
    fi
}

function run_main(){
    #获取总次数
    totalTimes=$(cat ${TESTPATH}/count_reboot.info |awk 'NR==1{print $0}')

    #获取执行次数
    frequencyTimes=$(cat ${TESTPATH}/count_reboot.info |awk 'NR==2{print $0}')

    #计算剩余次数
    remainingTimes=$(( $totalTimes - $frequencyTimes ))

    if [ $remainingTimes != 0 ];then
        #开启自动登录
        set_autoLogin
        sleep 1

        #开启自启服务
        reboot_server
        sleep 1

        #获取的执行次数+1 写入配置文件
        count=$(( $frequencyTimes + 1 ))
        sleep 1
        echo $frequencyTimes >> ${TESTPATH}/reboot.log
        sleep 1
        echo $count >> ${TESTPATH}/reboot.log
        sleep 1
        echo -e "$totalTimes\n$count" > ${TESTPATH}/count_reboot.info

        time=$(date +%Y%m%d_%H-%M-%S)
        echo  "$time  第 $count 次重启" >>  ${TESTPATH}/reboot.log
        sleep 1
        cat  ${TESTPATH}/reboot.log
        sleep 1
        #开始重启
        reboot
    elif [ $remainingTimes == 0 ];then
        echo "关闭自启服务，删除配置文件" >> ${TESTPATH}/reboot.log
        #关闭自动自动登录
        # off_autoLogin
        sleep 1
        #关闭自启服务
        systemctl disable test.service
        sleep 1
        #删除自启文件
        rm -rf $run_path
        #删除配置文件
        rm -rf ${TESTPATH}/count_reboot.info
        rm -rf ${TESTPATH}/wrietpath.sh
        rm -rf ${TESTPATH}/reboot.py
        echo "重启测试已经完成" >> ${TESTPATH}/reboot.log
        echo 1 | sudo -S dhclient
        #开启主自启服务
        systemctl enable daily.service
        #在重启一遍,继续执行daily.service
        reboot
    fi
}

run_main

'''
    if not os.path.exists("/home/uos/wrietpath.sh"):
        with open("/home/uos/wrietpath.sh","w",encoding="utf-8") as f1:
            f1.write(pathmesg)

    print("写入自启动服务")
    time.sleep(2)
    count = [str(count),"0"]
    if not os.path.exists("/home/uos/count_reboot.info"):
        with open("/home/uos/count_reboot.info","w",encoding="utf-8") as f2:
            for a in count:
                f2.write(a)
                f2.write("\n")

if __name__ == '__main__':
    # 切换目录到/home/uos/
    os.chdir("/home/uos/")
    if os.path.exists("/home/uos/count_reboot.info"):
        run_reboot()
    else:
        if len(sys.argv) == 2:
            count = 0
            try:
                count = int(sys.argv[1])
            except:
                print("参数错误")
                print('''

usage: sudo python3 [reboot.sh] <option> 
例如:
    执行 100 次重启
    sudo python3 reboot.sh 100

如果已经运行过上面的例子
可以不加参数运行
    sudo python3 reboot.sh
                ''')
                exit()

            if not os.path.exists("/home/uos/wrietpath.sh"):
                write_path(count)
            run_reboot()
    print("reboot finish")
    
