udplogger v0.8.0

udplogger - logging of UDP traffic
========= = ======= == === =======

Use of xml file to setup logging:
/etc/udplogger.xml

<!--This XML file describes the server to log from.
            <logger> Main element, do not change name
                <ip> IP-address of UDP server (0.0.0.0 for all ip)
                <port> UDP port
                <time> true or false add time information
                <folder> Path to store logfiles (only used in daemon mode)
-->

Runs as service or command line:

sudo systemctl start/stop/status udplogger.service

udplogger.py: logging of UDP traffic
Usage:
    mqttlogger.py <arguments>
        -h, --help    : Display this help
        -v, --version : Display version
        -d, --debug   : Debug communication
        -s, --service : Run as daemon
        <no arguments>: run as command line
        When running as command line, logging is to stdout

That's all for now ...

Please send Comments and Bugreports to hellyrulez@home.nl
