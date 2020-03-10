[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash

if [ -z "$1" ] ; then
	echo "Error: Missing argument mode (run,start,stop,set-apn)."
    exit 1
fi

if [ "$1" = "run" ] ; then
    while true; do
		# Check if modem is connected (/dev/ttyUSB0 does exist)
		if ls -la /dev/ttyUSB0 2>/dev/null; then
			# TODO: Run usb_modewitch rule for specifick surfsticks
			# Check if wvdial process is running
			if ! ps -C wvdial
	        then
	            echo ">>> No wvdial process running... Start WvDial to connect modem to internet."
	            wvdial &
	            time_started=`date +%s`
	        fi
		fi
        sleep 600
		# Kill a old wvdial process if ppp0 does not show up anymore
        #pppExists=$(ip link show ppp0 | grep -c UP)
        #if [ $pppExists != "1" ]; then
        #    time_stopped=`date +%s`
        #    time_running=$((time_stopped-time_started))
        #    echo ">>> ppp0 does not show up => Clean old processes. Runtime was $time_running seconds"
        #    killall wvdial
        #fi
        #sleep 5
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

    export APN
    # Create the config for wvdial
    cat /etc/wvdial.conf.tmpl | envsubst > /etc/wvdial.conf
else
    echo "Error: Unknown argument."
    exit 1
fi

exit 0
