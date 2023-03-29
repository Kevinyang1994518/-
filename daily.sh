#!/bin/bash

# 1.创建服务需要根用户权限
if [ $EUID != 0 ]; then
    echo "please run as root" 
    exit 0
fi

# 2.创建或者覆盖daily服务
testdir=`realpath $1`
reponame=$2
test_entry=$testdir/$reponame/loadtest.sh

service_path=/lib/systemd/system/daily.service
tee $service_path << EOF
[Unit]
Description=daily
After=network.target
After=lightdm.service
[Service]
Type=simple
ExecStart=/bin/bash $test_entry $testdir $reponame $3 $4 $5 $6 
User=uos
[Install]
WantedBy=multi-user.target
EOF

# 3.启动服务
systemctl daemon-reload
systemctl enable daily.service
reboot #以新内核启动，并且运行daily服务

