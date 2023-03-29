#!/bin/bash
# run only once

if [ $UID != 0 ];then echo run as root; exit 0; fi
echo "run as $ sudo bash addservice.sh ntimes"
sleep 5
service_path=/lib/systemd/system/powerstable.service
test_entry=/home/uos/power-stable/test.sh
tee $service_path << EOF
[Unit]
Description=powerstable
After=network.target
After=lightdm.service
[Service]
Type=simple
ExecStart=/bin/bash $test_entry s5 $1 $2 #节电模式(s3 s4 s5); 总次数(n); 日志存放处
User=uos
[Install]
WantedBy=multi-user.target
EOF

# 3.启动服务
rm -vf /home/uos/reboot_count
rm -vf /home/uos/reboot.log
systemctl daemon-reload
systemctl enable powerstable.service
systemctl start powerstable.service
