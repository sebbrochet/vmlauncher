#!/usr/bin/env python

import atexit
from pyVim import connect
from pyVmomi import vim

# List of properties.
# See: http://goo.gl/fjTEpW
# for all properties.
vm_properties = ["name", "config.uuid", "config.hardware.numCPU",
                 "config.hardware.memoryMB", "guest.guestState",
                 "config.guestFullName", "config.guestId",
                 "config.version"]

LAUNCHER_CUSTOM_FIELD= "vmlauncher_gid"

def connect_IFP(args):
    service_instance = None

    try:
       service_instance = connect.SmartConnect(host=args.target,
                                               user=args.user,
                                               pwd=args.password,
                                               port=int(args.port))
       atexit.register(connect.Disconnect, service_instance)
    except IOError as e:
       pass

    if not service_instance:
       raise SystemExit("Unable to connect to target with supplied info.")

    return service_instance

def get_custom_attribute_id(service_instance, custom_attribute_name):
    found = False
    custom_attribute_id = 0

    content = service_instance.RetrieveContent()
    for field_def in content.customFieldsManager.field:
        if field_def.name == custom_attribute_name:
           found = True
           custom_attribute_id = field_def.key
           break

    return found, custom_attribute_id

def print_vm_info(vm, custom_attribute_id, depth=1, max_depth=10):
    """
    Print information for a particular virtual machine or recurse into a
    folder with depth protection
    """

    # if this is a group it will have children. if it does, recurse into them
    # and then return
    if hasattr(vm, 'childEntity'):
        if depth > max_depth:
            return
        vmList = vm.childEntity
        for c in vmList:
            print_vm_info(c, depth + 1)
        return

    summary = vm.summary
    print "Name         : ", summary.config.name
    print "Path         : ", summary.config.vmPathName
    print "State        : ", summary.runtime.powerState

    if summary.customValue is not None:
        for value in summary.customValue: 
            if value.key == custom_attribute_id:
                print "Launcher GID : ", value.value
    print ""


def get_all_vm(service_instance, custom_attribute_id):
    def get_or_create_bucket(vm_dict, group_id):
        key = str(group_id)
        bucket = vm_dict.get(key, [])
        vm_dict[key] = bucket 

        return bucket
 
    vm_dict = {}

    content = service_instance.RetrieveContent()

    object_view = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [], True)
    for obj in object_view.view:
        if isinstance(obj, vim.VirtualMachine) and len(obj.value):
            for value in obj.value:
                if value.key == custom_attribute_id:
                    bucket = get_or_create_bucket(vm_dict, value.value)
                    bucket.append(obj)

    object_view.Destroy()
    return vm_dict

    
def start(args):
   print "start commandi %s" % args

def stop(args):
   print "Stop command %s" % args

def dry_start(args):
   service_instance = connect_IFP(args)
   found, custom_attribute_id = get_custom_attribute_id(service_instance, LAUNCHER_CUSTOM_FIELD)

   if not found:
      print "Custom attribute %s is not defined, please define it first in vCenter." % LAUNCHER_CUSTOM_FIELD
      return

   vm_dict = get_all_vm(service_instance, custom_attribute_id)
   print "VM: %s" % vm_dict

   #for obj in vm_list:
   #   print_vm_info(obj, custom_attribute_id)  

    
def dry_stop(args):
   print "DryStop commandi %s" % args
