[ -z $BASH ] && { exec bash "$0" "$@" || exit; }
#!/bin/bash
# file: update.sh
#
# This script will install required software for HoneyPi after an upgrade.
# It is recommended to run it in your home directory.
#

# check if sudo is used
if [ "$(id -u)" != 0 ]; then
    echo 'Sorry, you need to run this script with sudo'
    exit 1
fi

echo '>>> Running post-upgrade script...'
echo "postupdatefinished 1" >> /var/www/html/version.txt
