import csv
import json
import logging

from lapis.job import Job


def htcondor_job_reader(
    iterable,
    resource_name_mapping={  # noqa: B006
        "cores": "RequestCpus",
        "walltime": "RequestWalltime",  # s
        "memory": "RequestMemory",  # MiB
        "disk": "RequestDisk",  # KiB
    },
    used_resource_name_mapping={  # noqa: B006
        "queuetime": "QDate",
        "walltime": "RemoteWallClockTime",  # s
        "cores": "Number of Allocated Processors",
        "memory": "MemoryUsage",  # MB
        "disk": "DiskUsage_RAW",  # KiB
    },
    unit_conversion_mapping={  # noqa: B006
        "RequestCpus": 1,
        "RequestWalltime": 1,
        "RequestMemory": 1.024 / 1024,
        "RequestDisk": 1.024 / 1024 / 1024,
        "queuetime": 1,
        "RemoteWallClockTime": 1,
        "Number of Allocated Processors": 1,
        "MemoryUsage": 1 / 1024,
        "DiskUsage_RAW": 1.024 / 1024 / 1024,
    },
):
    input_file_type = iterable.name.split(".")[-1]
    if input_file_type == "json":
        htcondor_reader = json.load(iterable)
    elif input_file_type == "csv":
        htcondor_reader = csv.DictReader(iterable, delimiter=" ", quotechar="'")
    else:
        print("Invalid input file type {}. Job input file can not be read.".format(
            input_file_type))

    for entry in htcondor_reader:
        if float(entry[used_resource_name_mapping["walltime"]]) <= 0:
            logging.getLogger("implementation").warning(
                "removed job from htcondor import (%s)", entry
            )
            continue
        resources = {}
        for key, original_key in resource_name_mapping.items():
            try:
                resources[key] = float(entry[original_key]) \
                                 * unit_conversion_mapping.get(original_key, 1)
            except ValueError:
                pass
        used_resources = {
            "cores": (
                (float(entry["RemoteSysCpu"]) + float(entry["RemoteUserCpu"]))
                / float(entry[used_resource_name_mapping["walltime"]])
            )
            * unit_conversion_mapping.get(used_resource_name_mapping["cores"], 1)
        }
        try:
            inputfiles = {file["filename"]: file["usedsize"]
                          for file in entry["Inputfiles"]}
        except KeyError:
            inputfiles = dict()
        for key in ["memory", "walltime", "disk"]:
            original_key = used_resource_name_mapping[key]
            used_resources[key] = float(
                entry[original_key]
            ) * unit_conversion_mapping.get(original_key, 1)
        cpu_efficiency = (float(entry["RemoteSysCpu"]) +
                          float(entry["RemoteUserCpu"])) \
                         / float(entry[used_resource_name_mapping["walltime"]])
        yield Job(
            resources=resources,
            used_resources=used_resources,
            queue_date=float(entry[used_resource_name_mapping["queuetime"]]),
            cpu_efficiency=cpu_efficiency,
            inputfiles=inputfiles
        )
