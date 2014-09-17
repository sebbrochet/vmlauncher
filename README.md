## vmlauncher: Command-line client to send start/stop commands to a set of VMs in a VMWare vCenter host 

Let's say you're managing a VMWare vSphere farm and you need to start/stop of a set of VM in a specific order.    
You may use starting order that comes with a vApp but there're many limitations   
* vApp requires dedicated resources
* VApp can't depend on a another vApp
* ...

You may use only one vApp but it just doesn't scale.   

That's why I've designed vmlauncher that let's you specified a group order metadata (i.e `vmlauncher_gid`) for each of the VM you need to start/stop.    
When ordered, VM will be started sequentially, based on their group order id, from the lowest to the highest values.   
The same goes by for stop where VM are stoppped in reverse order.     
VM in the same group are started/stopped in parallel.   

Requirements
* linux box
* Python 2.6 or higher
* [pyvmomi](https://github.com/vmware/pyvmomi) library
* access to a VMWare vCenter host

Installation:
-------------
* Clone repository   
`git clone https://github.com/sebbrochet/vmlauncher.git`
* cd into project directory   
`cd vmlauncher`
* Install requirements with pip   
`pip install -r requirements.txt`
* Install vmlauncher binary   
`python setup.py install`

Usage:
------

```
usage: vmlauncher [-h] [-s SCOPE] [-u USER] [-p PASSWORD] [-t TARGET]
                  [-o PORT] [-r CLUSTER] [-c CONFIG] [-v]
                  command

Command-line client to send start/stop commands to a set of VMs in a VMWare vCenter host.

positional arguments:
  command               Command to execute (drystart, drystop, start, stop)

optional arguments:
  -h, --help            show this help message and exit
  -s SCOPE, --scope SCOPE
                        Limit command to act on scope defined in a file
  -u USER, --user USER  Specify the user account to use to connect to vCenter
  -p PASSWORD, --password PASSWORD
                        Specify the password associated with the user account
  -t TARGET, --target TARGET
                        Specify the vCenter host to connect to
  -o PORT, --port PORT  Port to connect on (default is 443)
  -r CLUSTER, --cluster CLUSTER
                        Specify the cluster name to run commands on (default
                        is all clusters)
  -c CONFIG, --config CONFIG
                        Configuration file to use (default is
                        '/etc/vmlauncher/vmlauncher.conf')
  -v, --version         Print program version and exit.
```

