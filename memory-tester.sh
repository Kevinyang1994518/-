#!/bin/bash

logpath=$1

install_and_run() {
    # install mem stress test tool 
    echo 1 | sudo -S apt install stressapptest -y

    # run with default options 
    # (all memory available, `nproc` number of threads, verbose level 8)
    stressapptest --stop_on_errors -l $logpath
}

build_and_run() {
    if [ ! -x /usr/bin/stressapptest ]; then
        git clone https://github.com/stressapptest/stressapptest.git
        cd stressapptest
        ./configure
        make
        echo 1 | sudo -S make install
    fi
    
    stressapptest --stop_on_errors -l $logpath
}

install_and_run || build_and_run