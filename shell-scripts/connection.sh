[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

if [ -z "$1" ] ; then
	echo "Error: Missing argument mode (run,start,stop,set-apn)."
    exit 1
fi

# global variables
time_started=`date +%s`

# functions
reconnect_modem () {
	PINGip=8.8.8.8
	TIMEOUT=15
	VENDOR=$1
	PRODUCT=$2
	# Reconnect device if no internet connection.
	if [ -z "$(/bin/ping -q -W$TIMEOUT -c1 $PINGip | grep '1 received')" ]; then
		echo ">>> $PINGip is not reachable. => Reconnecing device $VENDOR:$PRODUCT"
		for DIR in $(find /sys/bus/usb/devices/ -maxdepth 1 -type l); do
			if [[ -f $DIR/idVendor && -f $DIR/idProduct &&
						$(cat $DIR/idVendor) == $VENDOR && $(cat $DIR/idProduct) == $PRODUCT ]]; then
				echo 0 > $DIR/authorized
				sleep 0.5
				echo 1 > $DIR/authorized
			fi
		done
	else
		echo ">>> Ping $PINGip succeeded."
	fi
}

connect_modems () {
	usb_modeswitch -v 12d1 -p 14fe -V 12d1 -P 1506 -M "55534243123456780000000000000011060000000000000000000000000000"
}

kill_old_wvdial () {
	# Kill a old wvdial process if ppp0 does not show up anymore
	pppExists=$(ip link show ppp0 | grep -c UP)
	if [ $pppExists != "1" ]; then
			time_stopped=`date +%s`
			time_running=$((time_stopped-time_started))
			echo ">>> ppp0 does not show up => Clean old processes. Runtime was $time_running seconds"
			killall wvdial
	fi
}

start_wvdial () {
	# Check if modem is connected (/dev/ttyUSB0 does exist)
	if ls -la /dev/$ttyUSB 2>/dev/null; then
		# Check if wvdial process is running
		if ! ps -C wvdial
				then
						echo ">>> No wvdial process running... Start WvDial to connect modem to internet."
						wvdial &
						time_started=`date +%s`
				fi
	fi
}

# main routine
if [ "$1" = "run" ] ; then
    while true; do
		# Run usb_modewitch rule for specific surfsticks
		connect_modems
		# Check if wvdial process is running
		start_wvdial
    sleep 180
		# Kill a old wvdial process if ppp0 does not show up anymore
    kill_old_wvdial
    sleep 5
		reconnect_modem "12d1" "14dc"
		reconnect_modem "12d1" "1506"
    done
elif [ "$1" = "start" ] ; then
    wvdial &

elif [ "$1" = "stop" ] ; then
    killall wvdial

elif [ "$1" = "set-apn" ] ; then
    if [ -z "$2" ] ; then
    	echo "Warning: Missing argument APN."
        APN="pinternet.interkom.de" # default: NetzClub
    else
        APN="$2"
    fi

	if [ -z "$3" ] ; then
    	echo "Warning: Missing argument ttyUSB."
        ttyUSB="ttyUSB0" # default: ttyUSB0
    else
        ttyUSB="$3"
    fi

    export APN
	export ttyUSB
    # Create the config for wvdial
    cat /etc/wvdial.conf.tmpl | envsubst > /etc/wvdial.conf
else
    echo "Error: Unknown argument."
    exit 1
fi

exit 0
