# Table of Contents
1. [Installation](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#installation)
    1. [Requirements](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#requirements)
    2. [CORE Installation](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#core-installation) 
    3. [CORE Installation from Source (Less recommended)](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#core-installation-from-source-less-recommended)
    4. [Installing our Network Emulator](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#installing-our-network-emulator)
2. [Documentation](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#documentation)
3. [Usage](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#usage)
    1. [Topology Config File](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#topology-configuration-file)
    2. [Event Config File](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#event-configuration-file)
    3. [RESTAPI](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#restapi)
4. [FAQ](https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator/blob/master/README.md#faq)


# Installation

## Requirements
*  A system running a modern Linux
*  SUDO access 


## CORE Installation
In order to use this network emulator, you must first install [CORE](https://github.com/coreemu/core). 
 For the most up-to-date installation instructions for CORE, please refer to the [CORE documentation](https://coreemu.github.io/core/install.html). Otherwise, feel free to follow the instructions below.


CORE offers a python2 and python3 version. For different reason, our network emulator was at the beginning developed using the python2 version of CORE. However, since python2 is getting deprecated, this network emulator has been updated to support the python3 version of CORE (there might be some bugs remaining). For this reason, it is recommended to use the **python3** version of CORE now. 

Make sure python3 as well as pip for python3 are installed:

```bash
sudo apt install python3 python3-pip
```

This network emulator was developed using CORE version 5.3.1, however the latest version (as of the time of writing) [CORE 5.4.0](https://github.com/coreemu/core/releases/tag/release-5.4.0) is recommended. Simply follow the installation instructions for CORE at [CORE Installation](http://coreemu.github.io/core/install.html). The easiest way is to install CORE using the Debian packages as explained in the link, that should be all that is necessary to get CORE to work.

This is a summarized version of the steps required to install CORE from the packages:

1. Download the requirements.txt file and the core_python3_5.4.0_amd64.deb package from [CORE 5.4.0](https://github.com/coreemu/core/releases/tag/release-5.4.0). (A copy of these files is found in this repository under CORE-downloads as well).
2. CD to the directory containing the downloaded files and run the following commands:
    ```bash
    sudo python3 -m pip install -r requirements.txt
    sudo apt install ./core_python3_5.4.0_amd64.deb
    ```
    
Test your installation by running:

```bash
sudo core-daemon
```
or 
```bash
sudo systemctl status core-daemon
```   
in one terminal, and:
```bash
core-gui
```
in another and seeing if you get any errors. 


## CORE Installation from Source (Less recommended)
If your installation from the packages was successful, you can skip this step. 

If for some reason the package installation wasn't successful, installing from source is possible. If you choose to do that, there may be some extra steps that have to be taken for successful installation, such as manually installing certain dependencies and requirements, other than what is mentioned in the documentation:
1.  Run the following commands to install some required installation tools (See below for a one-liner command for the apt installs):   
    ```bash
    sudo apt-get update  
    sudo apt install git   
    sudo apt install bash bridge-utils ebtables ethtool xterm
    sudo apt install iproute2 libev-dev python tcl8.5 tk tk8.5 libtk-img     
    sudo apt install autoconf automake gcc libev-dev make python-dev python-setuptools gcc     
    sudo apt install libreadline-dev pkg-config imagemagick help2man
    ```
    
    One liner for apt install:
    ```bash
    sudo apt install git bash bridge-utils ebtables ethtool xterm iproute2 libev-dev python tcl8.5 tk tk8.5 libtk-img autoconf automake gcc libev-dev make python-dev python-setuptools gcc libreadline-dev pkg-config imagemagick help2man
    ```
    
    Install grpcio-tools: 
    ```bash
    pip3 install grpcio-tools 
    ```
    
2. Install necessary Python requirements - Go to [CORE-releases](https://github.com/coreemu/core/releases), download "requirements.txt", then cd to downloads folder and run one of the the following commands:
   ```bash
   # for python 2
   sudo python -m pip install -r requirements.txt
   # for python 3
   sudo python3 -m pip install -r requirements.txt
   
If for some reason, the requirements weren't found at the CORE github page, a copy of version 5.4.0 requirements can be found in this repository in the core-5.4.0 directory. 

3. Clone the CORE Version 5.4.0 source code to a directory of your choice:
    ```bash
    git clone https://github.com/rudyeila/core.git

NOTE: This repository is a fork I created of CORE version 5.4.0. You may install CORE from the latest source from the official [CORE repository](https://github.com/coreemu/core), however, I can't guarantee that everything will work properly.

4. cd into the cloned directory and run the following commands to install: 
    ```bash
    ./bootstrap.sh
    # use python2 or python3 depending on desired version - Python3 is recommended, as Python2 is getting deprecated. 
    PYTHON=VERSION ./configure # e.g. PYTHON=python3 ./configure
    make
    sudo make install

5. Install network tools to ensure a fully working CORE:
    ```bash
    sudo apt install quagga quagga-doc openssh-server isc-dhcp-server isc-dhcp-client vsftpd apache2 tcpdump radvd at ucarp openvpn ipsec-tools racoon traceroute mgen wireshark iperf3 tshark snmpd snmptrapd openssh-client
    ```                                                 
Try running CORE by typing **sudo core-daemon** in the console. If that worked, then your installation was probably successful. 

If you got an import error, then the path for the CORE library must be added to your python path. Installing CORE from the source, seems to install it locally for the user. Therefore, the CORE modules are most likely found under /usr/local/lib/python3/dist-packages/core. 

If that is the case, then you must add that path to your PYTHONPATH by adding the following line to the **~/.bashrc**  file and then **relaunch the console**:  
    
    
```bash
export PYTHONPATH="${PYTHONPATH}:/usr/local/lib/python3/dist-packages/"
```
    
With this, CORE should be successfully installed now. 

## Installing our Network Emulator
Once CORE is installed, our network emulator, which internally relies on CORE, can be installed. 

To do this, you need to clone this respository and cd into the Network Emulator folder:    

```bash
git clone https://gitlab2.informatik.uni-wuerzburg.de/descartes/iot-and-cps/iot-network-emulator.git
cd 2019_ba_rudy_ailabouni/NetworkEmulator/
```

Then you need to install some Python requirements. In the newly cloned repository, there should be a requirements.txt file. Run the following command:

```bash
sudo python3 -m pip install -r requirements.txt
```

If everything was installed successfully upto this point, you should now be done with the installation. 

# Documentation
For source code documentation, open [2019_ba_rudy_ailabouni/NetworkEmulator/docs/build/html/index.html](NetworkEmulator/docs/build/html/index.html) using a web browser. 

# Usage
The main entry point into the network emulator is the \_\_init\_\_.py module. You can start the emulator by running the following command as **super user** from the NetworkEmulator directory:

```bash
sudo python3 __init__.py
```
This would show the following help menu and initialize an empty emulation session, which can then be populated using the API:

```bash
This is the entry point into the emulator. You can either intitalize an empty
topology, or use a topology configuration file. Furthermore, if you wish, you
can provide an event configuration file to schedule the execution of certain
jobs at certain times.

optional arguments:
  -h, --help            show this help message and exit
  --topology TOPOLOGY, -t TOPOLOGY
                        Path to the topology configuration file (optional)
  --events EVENTS, -e EVENTS
                        Path to the event configuration file (optional)
  --start-scheduler [START_SCHEDULER], -s [START_SCHEDULER]
                        1 for True (defaults), 0 for False - Determines
                        whether the scheduler is immediately started with the
                        program or not. If not, you can start it later from
                        the API. Time zero would be right when the scheduler
                        is started.
```

If you provide no arguments, then an empty topolgoy with no event configuration file is initiated. For the format of the topology and event config files, refer to the relevant sections below.

## Topology Configuration File
You can use a topology configuration file to define the network topology. The file is structured as follows:

```yaml
topology:
    netmask: "10.0.0.0/24" # optional, defaults to "10.0.0.0/24"
    nodes:
        - name: <STRING> # node name
          type: <STRING> # node type - {host|switch|hub|(rj45/physical/phys)}
          interface: <STRING> # interface name to which the external physical computer is connected
                              # only required in case of an rj45 node
          ip: <STRING> # IP address (optional, only serves as a reference)
    links:
        - node1: <STRING> # name of first node in link
          node2: <STRING> # name of second node in link
```

This is an example of a such a config file, connecting two physical computers, left and right, which are connected to the emulator's host at the specified physical interface names, and are to be connected over a switch in the emulator:

```yaml
topology:
    netmask: 10.0.0.0/24 
    nodes:
        - name: subscriber
          type: host
        - name: publisher
          type: host
        - name: switch
          type: switch
        - name: left
          type: rj45
          interface: enp0s8
          ip: 10.0.0.3
        - name: right
          type: rj45
          interface: enp0s10
          ip: 10.0.0.4
    links:
        - node1: subscriber
          node2: switch
        - node1: publisher
          node2: switch
        - node1: left
          node2: switch
        - node1: right
          node2: switch
```

The network netmask specifies what sort of IP addresses should the virtual nodes within the emulator have. 

The nodes part defines the different nodes and their parameters, and the links part defines the actual connections between the nodes. It is always recommended to use switches to connect multiple nodes together. 

## Event Configuration File

The event configuration file defines different events that are executed by the scheduler at specific times. Each event takes a time parameter, which denotes the execution delay, from the moment the scheduler is started. 

Each event in the config file is structured as follows:

```yaml
event:
    type: <TimedEvent> # {LinkEvent|RunCMDEvent|OpenTermEvent}
    time: <FLOAT> <TimeUnit> # e.g 1000 ms or 3 seconds
    parameters:
        <param>: <value>
        <param>: <value>
        ...
        <param>: <value>  
---  # seperator between each event
event:
   ...    
```

To combine different events together, simply add three dashes (---) after each event definition and define the next one. The config.py module is a simple script that can be used to generate large but simple event configuration files. 


And each of the three supported events (LinkEvent|RunCMDEvent|OpenTermEvent) is defined as follows:

### LinkEvent
This event is resposnsible for updating the connection quality of a certain link.
```yaml
event:
    type: LinkEvent
    time: 2 seconds
    parameters:
        node1: subscriber
        node2: publisher
        link_params:
            delay: 10000 #  in microseconds
            bandwidth: 200000 #  in bits per second
            loss: 15 #  packet loss rate in %
            duplication: 10 #  packet duplication rate in %
            jitter: 5 # in microseconds
```

### RunCMD
This event executes a shell command at a certain node. 
```yaml
event:
    type: RunCMDEvent
    time: 20 seconds
    parameters:
        node: subscriber
        cmd: ping -c 3 10.0.0.2
        wait: False # Optional, defaults to True. True means that the program waits until the command finishes execution and returns the returned status code.
```

### OpenTerm
This event launches a root terminal window for a certain virtual node. Most useful when scheduler for time zero, since you'd have a terminal for the virtual node when the program starts. 
```yaml
event:
    type: OpenTermEvent
    time: 1 seconds
    parameters:
        node: subscriber
        shell: /bin/bash #  optional, defaults to "/bin/bash"
```

## RESTAPI

The best way to control the emulator is by using the RESTAPI. Our API currently only consists of a backend. Therefore, for the front-end it is recommend to use [Postman](https://www.getpostman.com/downloads/). Postman can be easily installed from the Ubuntu Software Center. 

Once it is installed, it is best to follow our RESTAPI documentation, which can be found at [RESTAPI-Docs](https://documenter.getpostman.com/view/8436185/SVfRtnYd?version=latest).

# FAQ
Q: When running the emulator, I get an error similar to: 
```python
FileExistsError: [Errno 17] File exists: '/tmp/pycore.1'
```
    
A: Run the CORE-cleanup script by typing core-cleanup in the console. Also, make sure you have no other emulation session running on the same device. In general, core-cleanup should fix a lot of issues. 

