#！/bin/bash

total=$1
logpath=$2

num=0
while [ $num -lt $total ]; do 
    echo 1 | sudo -S rtcwake -l -m disk -s 60  #60 秒后醒来
    echo 1 | sudo -S dmesg | egrep "error|failed|warning" >> $logpath #追加保留每次错误信息
    num=`expr $num + 1 `
    time=$(date +%Y%m%d_%H-%M-%S)
    echo "$time 第$num次测试。。。" | tee -a $logpath 
    if [ $num -ge $total ];then
        echo "完成休眠测试，总共$total次。" | tee -a $logpath
        break
    fi
done
