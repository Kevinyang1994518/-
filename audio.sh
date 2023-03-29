#!/bin/bash

file=$1
echo "test audio start!" > $file

checkCodecInitialization(){
    dmesg | egrep 'no codecs initialized | Unable to bind the codec'
    if [[ $? -eq 0 ]]; then
        echo "codec initialization fail" | tee -a $file
    else
        echo "codec initialization success" | tee -a $file
    fi
}

checkSoundCardDriverInsmod(){
    result=`lshw -c sound | grep driver= | awk -F '=' '{print $2}'| uniq`
    if [ -z "$result" ]
    then
      echo "sound card driver insmod fail" | tee -a $file
    else
      echo "sound card driver insmod success" | tee -a $file
    fi
}

checkSoundHardwareInfo(){
    alsactl init 2>&1 | grep "Hardware is initialized"
    if [[ $? -eq 0 ]]; then
        echo "check hardware information success" | tee -a $file
    else
        echo "check hardware information fail" | tee -a $file
    fi
}

volumeControl(){
    amixer set Master 23
    amixer scontents | grep 23
    if [[ $? -eq 0 ]]; then
        echo "set Playback volume success" | tee -a $file
    else
        echo "set Playback volume fail" | tee -a $file
    fi

    amixer set Capture 37
    amixer scontents | grep 37
    if [[ $? -eq 0 ]]; then
        echo "set Capture volume success" | tee -a $file
    else
        echo "set Capture volume fail" | tee -a $file
    fi
}

soundPlayback(){
    aplay -L | grep -w plughw | while read line
    do
        aplay -D $line -d 10 test.wav
        if [[ $? -eq 0 ]]; then
            echo "$line playback success" | tee -a $file
        else
            echo "$line playback fail" | tee -a $file
        fi
    done
}

echo "当前用户是：" 
whoami
if [[ $('whoami') == 'root' ]]; then
    echo "当前使用root用户执行"
else
    echo "请切换到root用户执行"
    sleep 3
    exit 1
fi

wget https://filewh.uniontech.com/seafhttp/files/70087843-1d64-44b5-873f-22fc41a8c327/fangjian.wav -O test.wav
if [[ ! -f test.wav ]]; then
    echo "音频文件不存在"
else
    echo "下载音频文件成功"
fi

checkCodecInitialization

checkSoundCardDriverInsmod

checkSoundHardwareInfo

volumeControl

soundPlayback
