#!/usr/bin/env python3

class VirtualMachine:
    def __init__(self, mob_id, vm_name, vcpu, vram_gb, vmdk_size_gb, vmdk_used_gb, os, os_name, partitions, ip_addresses, percent_cpu, percent_ram, iops, disk_throughput, net_pps, net_throughput):
        self.mob_id = mob_id
        self.vm_name = vm_name
        self.vcpu = vcpu
        self.vram_gb = vram_gb
        self.vmdk_size_gb = vmdk_size_gb
        self.vmdk_used_gb = vmdk_used_gb
        self.os = os
        self.os_name = os_name
        self.partitions = {}
        self.ip_addresses = []
        self.percent_cpu = percent_cpu
        self.percent_ram = percent_ram
        self.iops = iops
        self.disk_throughput = disk_throughput
        self.net_pps = net_pps
        self.net_throughput = net_throughput
