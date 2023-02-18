#!/usr/bin/env python3

# VMware Cloud Sizer Companion CLI - main module
################################################################################
### Copyright 2023 VMware, Inc.
### SPDX-License-Identifier: MIT License
################################################################################

import argparse
from argparse import SUPPRESS
import sys
from sizer_fxns import describe_import, default_import_sizing, custom_import_sizing

def main():
    class MyFormatter(argparse.RawDescriptionHelpFormatter):
        def __init__(self,prog):
            super(MyFormatter, self).__init__(prog,max_help_position=10)

    ap = argparse.ArgumentParser(
                    prog = 'sizer-cli.py',
                    description = 'A Command-line companion for the VMware Cloud Sizer.',
                    formatter_class=MyFormatter, usage=SUPPRESS,
                    epilog='''
                    Welcome to the VMC Sizer Companion CLI!! \n\n
                    This tool is used to help you send and receive sizing recommendations from the VMware Cloud Sizer quickly and reliably, with a number of available options.
                    The script acn be used to import data from from either RVTools or LiveOptics (DO NOT MODIFY the original files), or simply receive a 'quick sizing' from the sizer.
                    Use arguments at the command line to transform the data before you receive your sizing!\n\n
                    ''')

    # create a subparser for the subsequent sections    
    subparsers = ap.add_subparsers(help='sub-command help')

# ============================
# Parent parser containing arguments for all import operations
# ============================
    parent_import_parser = argparse.ArgumentParser(add_help=False)
    parent_import_parser.add_argument('-fn', '--file_name', required=True, help= 'The file containing the VM inventory to be imported.  By default, this script looks for the file in the "input" subdirectory.')
    parent_import_parser.add_argument('-ft', '--file_type', required=True, choices=['rv-tools', 'live-optics'], type=str.lower, help= 'Which tool completed the data collection?')

# ============================
# Parent parser containing arguments for all sizing operations
# ============================

    parent_sizing_parser = argparse.ArgumentParser(add_help=False)
    parent_sizing_parser.add_argument('-ct', '--cloud_type', choices=['VMC_ON_AWS', 'GCVE'], default = "VMC_ON_AWS", type=str.upper, help= 'Which cloud platform are you sizing for?')
    parent_sizing_parser.add_argument('-vp', '--vm_placement', action= "store_true", help= 'Use to show vm placement. Use to include VM placement data.')
    parent_sizing_parser.add_argument('-logs', '--calculation_logs', action= "store_true", help= 'Use to show calculation logs. Default is False - results will not, by default, show calculation logs.')
    parent_sizing_parser.add_argument('-o', '--output_format', choices=['csv', 'pdf', 'ppt', 'xls'], help= 'Select output format Default is none. ')

# ============================
# Subparsers for individual commands
# ============================

    # quick_sizing

    describe_parser = subparsers.add_parser('describe', formatter_class=MyFormatter, parents=[parent_import_parser], help='Describe the contents of an imported file.')
    describe_parser.set_defaults(func = describe_import)

    default_sizing_parser = subparsers.add_parser('default', formatter_class=MyFormatter, parents=[parent_import_parser,parent_sizing_parser], help='Import a file and receive a sizing recommendation without transforming data.')
    default_sizing_parser.set_defaults(func = default_import_sizing)

    custom_sizing_parser = subparsers.add_parser('custom', formatter_class=MyFormatter, parents=[parent_import_parser,parent_sizing_parser], help='Import a file and transform the data before receiving a sizing recommendation.')
    # custom_sizing_parser = subparsers.add_parser('custom', formatter_class=MyFormatter, help='Import a file and transform the data before receiving a sizing recommendation.')
    custom_sizing_parser.add_argument('-exfil', '--exclude_filter', nargs = '+', help = 'A list of text strings used to identify workloads to exclude.')
    custom_sizing_parser.add_argument('-eff', '--exclude_filter_field', choices = ['cluster','os','vmName'], help = 'The column/field used for exclusion filtering.')
    custom_sizing_parser.add_argument('-infil', '--include_filter', nargs = '+', help = 'A list of text strings used to identify workloads to keep.')
    custom_sizing_parser.add_argument('-iff', '--include_filter_field', choices = ['cluster','os','vmName'], help = 'The column/field used for inclusion filtering.')
    custom_sizing_parser.add_argument('-ps', '--power_state',  choices = ['p', 'ps'], type=str.lower, help = 'Use to specify whether to include only those (p)owered on, or powered on and suspended (ps).')
    custom_sizing_parser.add_argument('-wp', '--workload_profiles', choices=['all_clusters', 'some_clusters', 'os','vmName'], type=str.lower, help = 'Use to create workload profiles based on the selected grouping.')
    custom_sizing_parser.add_argument('-pl', '--profile_list', nargs = '+', help = 'A list of text strings used to filter workloads for the creation of workload profiles.')
    custom_sizing_parser.add_argument('-ir', '--include_remaining', action= 'store_true', help= 'Use to indicate you wish to keep remaining workloads - default is to discard.')   
    custom_sizing_parser.set_defaults(func = custom_import_sizing)

# ============================
# Parse arguments and call function
# ============================

    args = ap.parse_args()

    # If no arguments given, or no subcommands given with a function defined, return help:
    if 'func' not in args:
        ap.print_help(sys.stderr)
        sys.exit(0)
    else:
        pass

    params = vars(args)
    params.update({"input_path": 'input/'})
    params.update({"output_path": 'output/'})

    # Call the appropriate function with the dictionary containing the arguments.
    args.func(**params)
    sys.exit(0)

if __name__ == "__main__":
    main()
