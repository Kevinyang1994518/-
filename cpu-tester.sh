#!/bin/bash

# 需要使用sudo运行
if [ "$EUID" -ne 0 ]; then
    echo "need add sudo prefix"
    exit -1
fi

cpu_count=$(lscpu|grep "^CPU(s)"|awk '{print $2}')
wait=3

if [ ! -d /sys/devices/system/cpu ]; then
    echo "sysfs is not exist [/sys/devices/system/cpu], failed"
    exit -1
fi

i=1
while [ $i -lt $cpu_count ];
do
    if [ ! -f /sys/devices/system/cpu/cpu$i/online ]; then
        echo "sysfs is not exist [/sys/devices/system/cpu/cpu$i/online], failed"
        break
    fi

    #down test
    echo "cpu [$i] really to offline..."

    echo 0 > /sys/devices/system/cpu/cpu$i/online
    sleep $wait

    lscpu|grep "^Off-line CPU(s)"
    ret=$(lscpu | grep "^Off-line CPU(s)" | awk '{print $4}')
    if [ -z $ret ]; then
        ret=0
    fi

    if [ $ret -eq $i ]; then
        echo "cpu [$i] has been offline"
    else
        echo "cpu [$i] still online"
        break
    fi

    # up test
    echo "cpu [$i] really to up..."
    echo 1 > /sys/devices/system/cpu/cpu$i/online
    sleep $wait

    ret=$(lscpu | grep "^Off-line CPU(s)" | awk '{print $4}')
    if [ -z $ret ]; then
        echo "cpu [$i] has been online"
    else
        echo "cpu [$i] still offline"
    fi

    echo

    let i=$i+1
done