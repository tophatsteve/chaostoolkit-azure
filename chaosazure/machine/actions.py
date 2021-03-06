# -*- coding: utf-8 -*-
import random

from azure.mgmt.compute import ComputeManagementClient
from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from chaosazure import auth
from chaosazure.machine.constants import RES_TYPE_VM
from chaosazure.rgraph.resource_graph import fetch_resources

__all__ = ["delete_machine", "stop_machine", "restart_machine",
           "start_machine"]


def delete_machine(filter: str = None,
                   configuration: Configuration = None,
                   secrets: Secrets = None):
    """
    Delete a virtual machines at random.

    ***Be aware**: Deleting a machine is an invasive action. You will not be
    able to recover the machine once you deleted it.

    Parameters
    ----------
    filter : str
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
        Filtering example:
        'where resourceGroup=="myresourcegroup" and name="myresourcename"'
    """
    logger.debug(
        "Start delete_machine: configuration='{}', filter='{}'".format(
            configuration, filter))

    choice = __fetch_machine_at_random(filter, configuration, secrets)

    logger.debug("Deleting machine: {}".format(choice['name']))
    client = __init_client(secrets, configuration)
    client.virtual_machines.delete(choice['resourceGroup'], choice['name'])


def stop_machine(filter: str = None,
                 configuration: Configuration = None,
                 secrets: Secrets = None):
    """
    Stop a virtual machines at random.

    Parameters
    ----------
    filter : str
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
        Filtering example:
        'where resourceGroup=="myresourcegroup" and name="myresourcename"'
    """
    logger.debug(
        "Start stop_machine: configuration='{}', filter='{}'".format(
            configuration, filter))

    choice = __fetch_machine_at_random(filter, configuration, secrets)

    logger.debug("Stopping machine: {}".format(choice['name']))
    client = __init_client(secrets, configuration)
    client.virtual_machines.power_off(choice['resourceGroup'], choice['name'])


def restart_machine(filter: str = None,
                    configuration: Configuration = None,
                    secrets: Secrets = None):
    """
    Restart a virtual machines at random.

    Parameters
    ----------
    filter : str
        Filter the virtual machines. If the filter is omitted all machines in
        the subscription will be selected as potential chaos candidates.
        Filtering example:
        'where resourceGroup=="myresourcegroup" and name="myresourcename"'
    """
    logger.debug(
        "Start restart_machine: configuration='{}', filter='{}'".format(
            configuration, filter))

    choice = __fetch_machine_at_random(filter, configuration, secrets)

    logger.debug("Restarting machine: {}".format(choice['name']))
    client = __init_client(secrets, configuration)
    client.virtual_machines.restart(choice['resourceGroup'], choice['name'])


def start_machine(filter: str = None,
                  configuration: Configuration = None,
                  secrets: Secrets = None):
    """
    Start a virtual machine that is in a stopped state.

    Parameters
    ----------
    filter : str
        Filter the virtual machines. If the filter is omitted all stopped
        machines in the subscription will be started again.
        Filtering example:
        'where resourceGroup=="myresourcegroup" and name="myresourcename"'
    """

    logger.debug(
        "Start start_machine: configuration='{}', filter='{}'".format(
            configuration, filter))

    machines = __fetch_machines(filter, configuration, secrets)
    client = __init_client(secrets, configuration)
    stopped_machines = __fetch_stopped_machines(client, machines)
    __start_stopped_machines(client, stopped_machines)


###############################################################################
# Private helper functions
###############################################################################
def __start_stopped_machines(client, stopped_machines):
    for machine in stopped_machines:
        logger.debug("Starting machine: {}".format(machine['name']))
        client.virtual_machines.start(machine['resourceGroup'],
                                      machine['name'])


def __fetch_stopped_machines(client, machines):
    stopped_machines = []
    for m in machines:
        i = client.virtual_machines.instance_view(m['resourceGroup'],
                                                  m['name'])
        for s in i.statuses:
            status = s.code.lower().split('/')
            if status[0] == 'powerstate' and (
                    status[1] == 'deallocated' or status[1] == 'stopped'):
                stopped_machines.append(m)
                logger.debug("Found stopped machine: {}".format(m['name']))
    return stopped_machines


def __fetch_machines(filter, configuration, secrets):
    machines = fetch_resources(filter, RES_TYPE_VM, secrets, configuration)
    if not machines:
        logger.warning("No virtual machines found")
        raise FailedActivity("No virtual machines found")
    else:
        logger.debug(
            "Fetched virtual machines: {}".format(
                [x['name'] for x in machines]))
    return machines


def __fetch_machine_at_random(filter, configuration, secrets):
    machines = __fetch_machines(
        filter, configuration=configuration, secrets=secrets)
    choice = random.choice(machines)
    return choice


def __init_client(secrets, configuration):
    with auth(secrets) as cred:
        subscription_id = configuration['azure']['subscription_id']
        client = ComputeManagementClient(
            credentials=cred, subscription_id=subscription_id)

        return client
