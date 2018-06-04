#!/bin/bash -l

cd /home/debian/Git/GeckoBot/boot_autorun_test/
config-pin P9_28 pwm
config-pin P9_42 pwm
python load_pwm.py
python autorun_test.py
