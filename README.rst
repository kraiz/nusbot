Advanced Direct Connect (ADC) bot that connects to a hub and periodically
downloads the filelist of each user. When it find changes it will announce
these in the hub chat. It comes with chat commands that let you force scan
users and list a history of changes.

It's written in `Python <https://www.python.org>`_ and based on the great
`Twisted <https://twistedmatrix.com>`_ network framework.


Setup
-----

- Install virtualenv
  ::

    $ sudo apt-get install python-virtualenv python-pip

- Create a (python2-based) virtualenv (put it wherever you want it)
  ::

    $ virtualenv ~/.venv/nusbot

- Activate the virtualenv and install nusbot (together with its dependency twisted)
  ::

    $ source ~/.venv/nusbot/bin/activate
    (nusbot)$ pip install nusbot

- As it's a twisted plugin, you can run it via `twistd` (the Twisted Daemon Runner):
  ::

    (nusbot)$ twistd nusbot

- Check out the parameters:
  ::

    (nusbot)$ twistd nusbot --help

- Here's my systemd config (the `After=` line are dependencies, i like to start the vpn first):
  ::

    $ cat /etc/systemd/system/nusbot.service
    [Unit]
    Description=Nusbot: ADC Bot
    After=peervpn.service

    [Service]
    ExecStart=/home/myuser/.venv/nusbot/bin/twistd -n --pidfile= nusbot -h domain.or.ip.of.hub -d /home/myuser/.nusbot/nusbot.db
    Restart=always
    User=myuser

    [Install]
    WantedBy=multi-user.target

