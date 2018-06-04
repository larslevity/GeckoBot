#!/bin/bash -l

# In crontab -e add the following line to startz the script:
#@reboot /home/debian/Git/GeckoBot/boot_autorun_test/ssh_hack.sh 2>&1 | /home/debian/Git/GeckoBot/boot_autorun_test/timestamp.sh  >> /home/debian/Git/GeckoBot/boot_autorun_test/log/cronlog.log

faketty() {
    script -qfc "$(printf "%q " "$@")" /dev/null
}


faketty ssh -i ~/.ssh/rootkey -tt root@134.28.136.51 /home/debian/Git/GeckoBot/boot_autorun_test/start.sh
