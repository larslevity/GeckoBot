#!/bin/bash -l


faketty() {
    script -qfc "$(printf "%q " "$@")" /dev/null
}


# spawning a bash shell:
#/bin/bash -i -c "cd /home/debian/Git/GeckoBot/boot_autorun_test/ ; config-pin P9_28 pwm ; config-pin P9_42 pwm; python load_pwm.py ; python autorun_test.py&"

# spawning a python bash shell
# python -c 'import pty; pty.spawn("/bin/sh")' > cd /home/debian/Git/GeckoBot/boot_autorun_test/ ; config-pin P9_28 pwm ; config-pin P9_42 pwm ; python load_pwm.py ; python autorun_test.py& 

# test
# python -c 'import pty; pty.spawn("/bin/sh", "ls")'
#faketty python /home/debian/Git/GeckoBot/boot_autorun_test/autorun_test.py
# faketty python -c "import sys; print sys.stdout.isatty()" | cat




cd /home/debian/Git/GeckoBot/boot_autorun_test/
config-pin P9_28 pwm
config-pin P9_42 pwm
python load_pwm.py
python autorun_test.py
