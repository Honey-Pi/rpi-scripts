`sudo nano /etc/rc.local`

Vor die zeile `exit 0` folgendes einfügen:

```
# Run HoneyPi
(sleep 10;python3 /home/pi/rpi-scripts/main.py)&
```



### Fix autostart issue `raspbian failed to start /etc/rc.local compatibility` after raspbian update
`sudo nano /etc/rc.local`

```
#!/bin/sh -x
to
#!/bin/bash
```


* Testing if `rc.local` works: `sudo sh -x /etc/rc.local`