#!/bin/bash

echo "Start getting hardware information."

if [[ $EUID -ne 0 ]]; then
	echo "Error:This script must be run as root!" 1>&2
	exit 1
fi

# check network


echo install acpica-tools dmidecode
apt install -y acpica-tools dmidecode

echo dump apci table
acpidump > acpi.out
acpixtract -a acpi.out
iasl -d dsdt.dat

echo get dmi info
dmidecode > dmi.info

echo get pci info
lspci > pci.info
lspci -vv  >> pci.info

echo get usb info
lsusb > usb.info
lsusb -v >> usb.info

echo get kernel log
dmesg > kernel.log
dmesg -l 3 > kernel_err.log

echo get interrupt info
cat /proc/interrupts > interrupts.info

echo get cpu info
lscpu > cpu.info

echo get kernel config
cp /boot/config* ./

# echo "The collection is complete, please pack and save this folder."
chown -R uos:uos ./*
