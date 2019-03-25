import csv
import logging

from lapis.job import Job


def htcondor_job_reader(iterable, resource_name_mapping={
    "cores": "RequestCpus",
    "walltime": "RequestWalltime",
    "memory": "RequestMemory",
    "disk": "RequestDisk"
}, used_resource_name_mapping={
    "queuetime": "QDate",
    "walltime": "RemoteWallClockTime",
    "cores": "Number of Allocated Processors",
    "memory": "MemoryUsage",
    "disk": "DiskUsage_RAW"
}):
    htcondor_reader = csv.DictReader(iterable, delimiter=' ', quotechar="'")

    for row in htcondor_reader:
        if float(row[used_resource_name_mapping["walltime"]]) <= 0:
            logging.getLogger("implementation").warning("removed job from htcondor import", row)
            continue
        resources = {}
        for key in resource_name_mapping:
            try:
                resources[key] = float(row[resource_name_mapping[key]])
            except ValueError:
                pass
        yield Job(
            resources=resources,
            used_resources={
                "cores": (float(row["RemoteSysCpu"]) + float(row["RemoteUserCpu"])) /
                         float(row[used_resource_name_mapping["walltime"]]),
                "memory": float(row[used_resource_name_mapping["memory"]]),
                "walltime": float(row[used_resource_name_mapping["walltime"]]),
                "disk": float(row[used_resource_name_mapping["disk"]])
            }, queue_date=float(row[used_resource_name_mapping["queuetime"]]))
