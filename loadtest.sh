#!/bin/bash

ATTestDir=$1
test_repo_name=$2
codepath=$ATTestDir/$test_repo_name
sleep_n=$3; hiber_n=$4; reboot_n=$5; ltp_t=$6

step1=1.硬件检查并测试
step2=2.头道驱动功能测试
step3=3.电源稳定性测试
step4=4.二次驱动功能测试
step5=5.LTP压力测试

echo -e \
"================================
开始内核每日测试
测试分为5个部分
    $step1
    $step2
    $step3
    $strp4
    $step5
================================"

# 1. 硬件检查并测试
hardware_test(){
echo -e \
"================================
    $step1
        1) HW-info
        2) cpu test
        3) cpufreq test
        4) stressapptest
================================"
    if [ ! -d $ATTestDir/output/hwinfo ]; then 
        echo "================ 1) hw-info 收集 ================"
        mkdir -p $ATTestDir/output/hwinfo && cd $ATTestDir/output/hwinfo
        echo 1 | sudo -S bash $codepath/script/hardware_information.sh
        echo "================ 1) hw-info 收集 结束 ================"
    fi
    if [ ! -f $ATTestDir/output/cpu.log ]; then
        echo "================ 2) cpu test ================"
        cd $ATTestDir/output
        echo 1 | sudo -S bash $codepath/script/cpu-tester.sh | tee cpu.log
        echo "================ 2) cpu test 结束 ================"
    fi
    if [ ! -f $ATTestDir/output/cpufreq.log ]; then
        echo "================ 3) cpufreq test ================"
        cd $ATTestDir/output
        echo 1 | sudo -S bash $codepath/script/cpufreq-tester.sh | tee cpufreq.log
        echo "================ 3) cpufreq test 结束 ================"
    fi
    if [ ! -f $ATTestDir/output/memtest.log ]; then
        echo "================ 4) stressapptest ================"
        mkdir -p $ATTestDir/extRepo && cd $ATTestDir/extRepo
        bash $codepath/script/memory-tester.sh $ATTestDir/output/memtest.log #可能会在extRepo中克隆源码进行编译安装
        echo "================ 4) stressapptest 结束 ================"
        sleep 3
    fi
}

run_nettest(){
    echo "================ $1 1) Net ================"
    mkdir -p $2 && cd $2
    g++ $codepath/script/nettest.cpp -o ./nettest
    echo 1 | sudo -S ./nettest
    rm ./nettest
    echo 1 | sudo -S chown -R uos:uos ./*
    echo "================ $1 1) Net 结束 ================"
}

run_audiotest(){
    echo "================ $1 2) Audio ================"
    cd $ATTestDir/output
    echo 1 | sudo -S bash $codepath/script/audio.sh $2
    ls -l test.wav # cat log to check download
    rm ./test.wav
    echo "================ $1 2) Audio 结束 ================"
}

# 2. 头道驱动功能测试 / 4. 二次驱动功能测试
driver_test(){
step=$1
if [ $step == $step2 ];then
    netlogdir=$ATTestDir/output/nettest-1
    audiolog=audio-1.log
elif [ $step == $step4 ]; then
    netlogdir=$ATTestDir/output/nettest-2
    audiolog=audio-2.log
else
    echo unexpected step: $step
    exit 0
fi
echo -e \
"================================
    $step
        1) 网络
        2) 声卡
        3) 显卡           (x)
        4) 外设usb、pci   (x)
================================"
    if [ ! -d $netlogdir ]; then
        run_nettest $step $netlogdir
    fi
    if [ ! -f $ATTestDir/output/$audiolog ]; then
        run_audiotest $step $audiolog
    fi
    return 0
}

run_s3() {
    if [ `arch` == 'x86_64' -o `arch` == 'loongarch64' ]; then
        cd $ATTestDir/output
        echo "================ 1) Sleep (S3) ================"
        sleep 2
        bash $codepath/script/S3.sh $1 S3.log #$1 次数
    elif [ `arch` == 'arm64' ]; then
        echo "not sure for arm64, depend on hardware"
        return 1
    else
        echo "arch $(arch) not support"
        return 2
    fi
    echo 1 | sudo -S dhclient
    sleep 20
    echo "================ S3结束 ================"
    return 0
}
run_s4() {
    if [ `arch` == 'x86_64' -o `arch` == 'loongarch64' ]; then
        cd $ATTestDir/output
        echo "================ 2) Hibernate (S4) ================"
        sleep 2
        bash $codepath/script/S4.sh $1 S4.log #$1 次数
    elif [ `arch` == 'arm64' ]; then
        echo "not sure for arm64, depend on hardware"
        return 1
    else
        echo "arch $(arch) not support"
        return 2
    fi
    echo 1 | sudo -S dhclient
    sleep 20
    echo "================ S4结束 ================"
    return 0
}
run_s5() {
    if [ -x "/sbin/reboot" ]; then
        if [ ! -d /home/uos ]; then
            return 1
        fi
        reboot_codedir=/home/uos/power-stable
        if [ ! -d $reboot_codedir ]; then
            mkdir $reboot_codedir
            mv $codepath/script/addservice.sh $reboot_codedir
            mv $codepath/script/test.sh $reboot_codedir
        fi
        cd $reboot_codedir
        echo "================ 3) Reboot (S5) ================"
        echo 1 | sudo -S systemclt disable daily.service 
        echo 1 | sudo -S bash addservice.sh $1 $ATTestDir/output/reboot.log
        # system reboot， stop here， resume in test.sh
    else
        return 2 # not support reboot
    fi
}

# 5. LTP压力测试
run_ltp(){
    echo "================ $step5 ================"
    mkdir -p $ATTestDir/extRepo && cd $ATTestDir/extRepo
    sudo python3 $codepath/script/ltp.py -p $1
    mv -v /home/uos/ltp.log $ATTestDir/output
    echo "================ $step5 结束 ================"
}



load_reload(){
    hardware_test
    driver_test $step2
    echo "================ $step3 ================"
    run_s3 $1 $2
    run_s4 $3 $4
    if ( [ -f /home/uos/reboot.log ]  && tail -1 /home/uos/reboot.log | grep "完成" ); then
        mv -v /home/uos/reboot.log $ATTestDir/output/reboot.log
        echo "================ S5结束 ================"
        echo "================ $step3 结束 ================"
    else
        run_s5 $5
    fi

    sleep 5
    echo "重启完成，进行驱动功能测试"
    driver_test $step4

    sleep 5
    echo "驱动功能测试完成，进行LTP"
    run_ltp $6

    #关闭服务
    echo 1 | sudo -S systemctl disable daily.service
    echo 1 | sudo -S rm /lib/systemd/system/daily.service
    journalctl -u daily.service -S today > $ATTestDir/output/jounal.log

    #收集日志 parse.py
    python3 $codepath/parse.py $ATTestDir/output
}

load_reload $sleep_n $sleep_t $hiber_n $hiber_t $reboot_n $ltp_t
