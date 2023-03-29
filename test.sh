#!/bin/bash

mode=$1
total=$2
logpath=$3

countfile=/home/uos/reboot_count
logfile=/home/uos/reboot.log

echo 调用test.sh

if [ $mode == s3 ];then
    exit
elif [ $mode == s4 ]; then
    exit
elif [ $mode == s5 ]; then
    if [ -f $countfile ];then # in progress
        totalTimes=$(awk 'NR==1{print $0}' $countfile)
        alreadyTimes=$(awk 'NR==2{print $0}' $countfile)
        echo 1 | sudo -S dmesg | egrep "fail|error|warn" >> $logfile
        echo $(date +"%Y-%m-%d %H:%M:%S") 第 $alreadyTimes 次重启。。。 | tee -a $logfile
        echo sleep 10; sleep 10
        if [ $alreadyTimes -lt $totalTimes ]; then # next round
            echo $totalTimes > $countfile
            alreadyTimes=`expr $alreadyTimes + 1`
            echo $alreadyTimes >> $countfile
            echo 1 | sudo -S reboot
        else					   # finish
            rm $countfile
            echo 已完成 $total 次重启。。。 >> $logfile
            echo 1 | sudo -S systemctl disable powerstable.service
            mv -v $logfile $logpath #日志放到指定目录下
            echo 1 | sudo -S systemctl enable daily.service
            echo 1 | sudo -S systemctl start daily.service
        fi
    else				      # initialize
        echo $total > $countfile
        echo 1 >> $countfile
        echo 10秒后开始重启; sleep 10
        echo 1 | sudo -S reboot
    fi
else
    exit
fi
