#!/bin/bash

# 需要使用sudo运行

if [ "$EUID" -ne 0 ]; then
    echo "need add sudo prefix"
    exit -1
fi

version=$(uname -r)
kconfig=/boot/config-$version
cpu_count=$(lscpu|grep "^CPU(s)"|awk '{print $2}')
wait=3
i=0

detect_kconfig_cpufreq_support()
{
    configs=$(grep CPU_FREQ $kconfig | grep -v ^#)
    for line in $configs
    do
        cfg_name=$(echo $line | awk -F "=" '{print $1}')
        cfg_val=$(echo $line | awk -F "=" '{print $2}')
        printf "\033[31m%-32s\t\t\t\t%4s\033[0m\n" $cfg_name $cfg_val
        if [ $cfg_name == "CONFIG_CPU_FREQ" ]; then
            if [ $cfg_val != "y" -a $cfg_val != "m" ]; then
                echo "cpufreq is not support, failed"
                return -1;
            fi
        fi
    done
    return 0
}

detect_sysfs_cpufreq_support()
{
    err=0
    while [ $i -lt $cpu_count ];
    do
        if [ ! -d /sys/devices/system/cpu/cpu$i/cpufreq/ ];then
            echo "sysfs is not exists [/sys/devices/system/cpu/cpu$i/cpufreq/]"
            err=1
            break
        fi

        if [ ! -f /sys/devices/system/cpu/cpu$i/cpufreq/scaling_available_governors ]; then
            echo -e "cpu[$i]\tnot support modify cpufreq via sysfs"
            err=2
            let i=$i+1
            continue;
        fi

        ret=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_available_governors)
        echo -e "cpu[$i]\tsupport [$ret]"

        if [ -f /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor ]; then
            ret=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor)
            echo -e "\tcurrent gov: [$ret]"
        fi

        if [ -f /sys/devices/system/cpu/cpu$i/cpufreq/cpuinfo_cur_freq ]; then
            ret=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/cpuinfo_cur_freq)
            echo -e "\tcurrent freq: [$ret]"
        fi

        if [ -f /sys/devices/system/cpu/cpu$i/cpufreq/scaling_driver ]; then
            ret=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/scaling_driver)
            echo -e "\tcurrent scaling_driver: [$ret]"
        fi

        if [ -f /sys/devices/system/cpu/cpu$i/cpufreq/stats/total_trans ]; then
            ret=$(cat /sys/devices/system/cpu/cpu$i/cpufreq/stats/total_trans)
            echo -e "\ttotal_trans times: [$ret]"
        fi

        let i=$i+1
    done
    return $err
}

echo "[ 1. detect kernel config support for cpufreq... ]"
detect_kconfig_cpufreq_support
ret=$?
echo "[ detect kernel config support for cpufreq done ]"

if [ $ret -eq -1 ]; then
    exit -1
fi

echo
echo "[ 2. detect sysfs support for cpufreq... ]"
detect_sysfs_cpufreq_support
ret=$?
echo "[ detect sysfs support for cpufreq done ]"
echo
if [ $ret -ne 0 ]; then
    exit -1
fi

