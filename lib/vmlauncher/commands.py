#!/usr/bin/env python
# -*- coding: utf-8 -*-

import atexit
from pyVim import connect
from pyVmomi import vim, vmodl


LAUNCHER_CUSTOM_FIELD = "vmlauncher_gid"


def myprint(unicodeobj):
    import sys
    print unicodeobj.encode(sys.stdout.encoding or 'utf-8')


def get_service_instance(args):
    service_instance = None

    try:
        service_instance = connect.SmartConnect(host=args.target,
                                                user=args.user,
                                                pwd=args.password,
                                                port=int(args.port))
        atexit.register(connect.Disconnect, service_instance)
    except IOError as e:
        pass
    except vim.fault.InvalidLogin, e:
        raise SystemExit("Error: %s" % e.msg)

    if not service_instance:
        raise SystemExit("Error: unable to connect to target with supplied info.")

    return service_instance


def get_all_vm(service_instance, custom_attribute_name, cluster_name):
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

    def get_or_create_bucket(vm_dict, group_id):
        key = str(group_id)
        bucket = vm_dict.get(key, [])
        vm_dict[key] = bucket

        return bucket

    def get_dict_with_vm(custom_attribute_id, cluster_name):
        def is_in_cluster(vm, cluster_name):
            return cluster_name == '' or get_full_name(vm).split('/')[1] == cluster_name

        vm_dict = {}
        content = service_instance.RetrieveContent()
        object_view = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)

        for vm in object_view.view:
            for value in vm.value:
                if value.key == custom_attribute_id and value.value and is_in_cluster(vm, cluster_name):
                    bucket = get_or_create_bucket(vm_dict, value.value)
                    bucket.append(vm)

        object_view.Destroy()

        return vm_dict

    found, custom_attribute_id = get_custom_attribute_id(service_instance, custom_attribute_name)

    if not found:
        raise SystemExit('Error: custom attribute "%s" is not defined, please define it first in vCenter' % custom_attribute_name)

    vm_dict = get_dict_with_vm(custom_attribute_id, cluster_name)
    vm_list_by_gid = [[key, vm_dict[str(key)]] for key in sorted([int(k) for k in vm_dict.keys()])]

    return vm_list_by_gid


def get_full_name(vm):
    current = vm
    full_name = vm.name

    while hasattr(current, 'parentVApp'):
        full_name = "%s/%s" % (current.parentVApp.name, full_name)
        current = current.parentVApp

    while hasattr(current, 'parent'):
        full_name = "%s/%s" % (current.parent.name, full_name)
        current = current.parent

    return full_name


def display_all_vm(vm_list_by_gid):
    def display_vm(vm):
        myprint("%s (%s) - %s" % (vm.name, get_full_name(vm), vm.summary.runtime.powerState))

    for gid, vm_list in vm_list_by_gid:
        print "%d:" % gid

        for vm in vm_list:
            display_vm(vm)

        print ""

def WaitForTasks_IFN(tasks, si, callback = None):
   if tasks:
       WaitForTasks(tasks, si, callback)

def WaitForTasks(tasks, si, callback = None):
   """
   Given the service instance si and tasks, it returns after all the
   tasks are complete
   """

   pc = si.content.propertyCollector

   taskList = [str(task) for task in tasks]

   # Create filter
   objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task) for task in tasks]
   propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task, pathSet=[], all=True)
   filterSpec = vmodl.query.PropertyCollector.FilterSpec()
   filterSpec.objectSet = objSpecs
   filterSpec.propSet = [propSpec]
   filter = pc.CreateFilter(filterSpec, True)

   try:
      version, state = None, None

      # Loop looking for updates till the state moves to a completed state.
      while len(taskList):
         update = pc.WaitForUpdates(version)
         for filterSet in update.filterSet:
            for objSet in filterSet.objectSet:
               task = objSet.obj
               for change in objSet.changeSet:
                  if change.name == 'info':
                     state = change.val.state
                  elif change.name == 'info.state':
                     state = change.val
                  else:
                     continue

                  if not str(task) in taskList:
                     continue

                  if state == vim.TaskInfo.State.success:
                     # Remove task from taskList
                     taskList.remove(str(task))
                     if callback:
                         callback(task)
                  elif state == vim.TaskInfo.State.error:
                     raise task.info.error
         # Move to next version
         version = update.version
   finally:
      if filter:
         filter.Destroy()


def start_all_vm(service_instance, vm_list_by_gid):
    def on_vm_started(task):
        print "%s started" % task.info.entityName 

    def start_vm_IFN(vm):
        task = None

        if vm.summary.runtime.powerState == "poweredOff":
             print "Starting %s..." % vm.name
             task = vm.PowerOn()
        else:
             print "%s is already powered ON" % vm.name

        return task

    for gid, vm_list in vm_list_by_gid:
        print "Starting group %d..." % gid

        tasks = []

        for vm in vm_list:
            task = start_vm_IFN(vm)
            if task:
                tasks.append(task)    

        WaitForTasks_IFN(tasks, service_instance, on_vm_started)

        print ""


def start(args):
    service_instance = get_service_instance(args)
    vm_list_by_gid = get_all_vm(service_instance, LAUNCHER_CUSTOM_FIELD, args.cluster)

    try:
        start_all_vm(service_instance, vm_list_by_gid)
    except vmodl.MethodFault as e:
        raise SystemExit("Error: caught vmodl fault : " + e.msg)
    except Exception as e:
        raise SystemExit("Error: caught Exception : " + str(e))

def dry_start(args):
    service_instance = get_service_instance(args)
    vm_list_by_gid = get_all_vm(service_instance, LAUNCHER_CUSTOM_FIELD, args.cluster)

    display_all_vm(vm_list_by_gid)


def dry_stop(args):
    service_instance = get_service_instance(args)
    vm_list_by_gid = get_all_vm(service_instance, LAUNCHER_CUSTOM_FIELD, args.cluster)[::-1]

    display_all_vm(vm_list_by_gid)


def stop_all_vm(service_instance, vm_list_by_gid):
    def on_vm_shutdown_guest(task):
        print "%s guest stopped" % task.info.entityName
    def on_vm_stopped(task):
        print "%s stopped" % task.info.entityName

    def shutdown_guest_IFN(vm):
        task = None

        if vm.runtime.powerState == "poweredOn" and vm.guest.toolsStatus == 'toolsOk':
            print "Shutting down guest on %s..." % vm.name
            task = vm.ShutdownGuest()

        return task

    def stop_vm_IFN(vm):
        task = None

        if vm.runtime.powerState == "poweredOn":
            print "Stopping %s..." % vm.name
            task = vm.PowerOff()
        else:
            print "%s is already powered OFF" % vm.name

        return task

    for gid, vm_list in vm_list_by_gid:
        print "Stopping group %d..." % gid

        tasks = []

        for vm in vm_list:
            task = shutdown_guest_IFN(vm)
            if task:
                tasks.append(task)

        WaitForTasks_IFN(tasks, service_instance, on_vm_shutdown_guest)

        tasks = []

        for vm in vm_list:
            task = stop_vm_IFN(vm)
            if task:
                tasks.append(task)

        WaitForTasks_IFN(tasks, service_instance, on_vm_stopped)

        print ""


def stop(args):
    service_instance = get_service_instance(args)
    vm_list_by_gid = get_all_vm(service_instance, LAUNCHER_CUSTOM_FIELD, args.cluster)[::-1]

    try:
        stop_all_vm(service_instance, vm_list_by_gid)
    except vmodl.MethodFault as e:
        raise SystemExit("Error: caught vmodl fault : " + e.msg)
    except Exception as e:
        raise SystemExit("Error: caught Exception : " + str(e))

