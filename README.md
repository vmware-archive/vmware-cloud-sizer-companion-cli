# pyVMC Sizer
A python client 'companion' tool for sizing workloads for migration to VMware Cloud.

## 1.1 What is the pyVMC Sizer?
Welcome to the Python Client for VMware Cloud Sizer!  pyVMC Sizer is a Python tool developed for assisting customers, consultants, presales engineers, and anyone else for sizing workloads for VMware Cloud.

## 1.2 Overview

PyVMC was created by Tom Twyman and Chris White.  This tool can be used to help you quickly and reliably retrieve sizings for VMware Cloud via the command line.  It is intended primarily as a tool to take file data - either from RVTools or LiveOptics - and either immediately retrieve a sizing recommendation, or to allow the user to transform the data (using a set of predefined transformations) before retrieving a recommendation.

## 1.3 Features
Current 'out of the box' capabilities include:
* ingest either a LiveOptics or RVTools file
* get a sizing recommendation for it
* optionally create workload profiles based on current vm:cluster distribution
* creating workload profiles based on existing clusters
* selecting some or all existing clusters to use for sizing
* including all VM, or only those powered on / suspended
* present results on-screen
* optionally save to PDF as well
* provide a quick review, the "view_only" option just quickly summarizes contents of the file.


## 1.4 Getting Started

### 1.4.1 Install Python
This tool is dependent on Python3 (specifically 3.10), you can find installation instructions for your operating system in the Python documentation (https://wiki.python.org/moin/BeginnersGuide/Download).

### 1.4.2 Download code
If you know git, clone the repo with

```git clone https://github.com/maulepilot117/pyvmcsizer.git ```


### 1.4.3 Install Python modules and packages
When you navigate to the pyvmcsizer folder, you will find a requirements.txt file that lists all your Python packages. They can all be installed by running the following command on Linux/Mac:

```pip3 install -r requirements.txt```

On Windows, use

```python -m pip install -r requirements.txt```

### 1.4.5 Do I need to know Python?
No! You can simply use it interactively at the command line, or in a script.

## 1.5 Running the Script
This is super easy...
- run ./sizerimporter.py to see the current list of supported commands.
- use '-h' to see the supported arguments / parameters.

## 1.6 Project Structure

For those of you interested in getting 'under the covers,' this project is split up amongst several files.

![Structure of pyVMC Sizer](pyvmcsizer.png)

* sizerimporter.py - contains the _main_ function, which defines all the arguments accepted, help for the command, etc.  It also makes calls to other functions based on what arguments are passed
* sizer_json.py - functions that call the VMware Cloud Sizer API - specifically for parsing an Excel file and obtaining a sizing recommendation.
* data_transform.py - functions that ingest data from an Excel file (LiveOptics or RVTools), and optionally transform the data before sending it to the sizer for a recommendation
* sizer_output.py - functions to handle the output of data


