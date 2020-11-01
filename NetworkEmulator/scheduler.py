#!/usr/bin/python

'''
    This module contains th elogic for the scheduler
    The scheduler used is the APScheduler
'''


import os
import subprocess
import time
from datetime import datetime, timedelta
from collections import OrderedDict

from apscheduler.schedulers.background import BackgroundScheduler

from events import LinkEvent, RunCMDEvent, OpenTermEvent


class Scheduler(object):
    '''
        Our implementation of the scheduler intenrally initiaties an APScheduler.BackgroundScheduler
    '''

    def __init__(self, events=None, topology=None):
        '''
            Creates an instance of the scheduler

            :param scheduler: reference to the APScheduler instance
            :type scheduler: APScheduler.BackgroundScheduler

            :param start_time: The time of when the scheduler begins to scheduler the events. Is used as a reference to normalize the execution time such that this is time 0.
            :type start_time: datetime.datetime

            :param is_started: a boolean that is used to determine whether the scheduler has been started or not
            :type is_started: boolean

            :param events: a list of TimedEvent objects, i.e. the events that are to be schedule.
            :type events: list[events.TimedEvent]

            :param topology: a reference to the Topology class that is used to schedule calls to Topology class methods.
            :type topology: NetworkEmulator.Topology
        '''
        self.scheduler = BackgroundScheduler()
        self.start_time = None  # Will be set when we beging scheduling events
        self.is_started = False
        self.events = events
        self.topology = topology

    def schedule_events(self, events, topology):
        '''
            This method is used to schedule the different events. Since the APScheduler takes a datetime object for the execution time, we need to convert the event times to dates.
            We do this by taking a reference of the start_time and then calling the method _calculate_new_time which creates a time delta object between the events execution time and the start_time
            of the scheduler. This time deta object can then be converted to an ISO datetime object.

            To add more events to the scheduler, you need to define a class for the new events in the events.py module, add the logic to the parser and then add an if statement in this method,
            along with the required logic for execution.
        '''
        self.start_time = datetime.now()
        for event in events:
            if (isinstance(event, LinkEvent)):
                self.scheduler.add_job(topology.update_link, 'date', run_date=self._calculate_new_time(event.execution_delay),
                                       args=event.args)
            elif (isinstance(event, RunCMDEvent)):
                self.scheduler.add_job(topology.get_node_by_name(
                    event.node_name).run_cmd, 'date', run_date=self._calculate_new_time(event.execution_delay), args=event.args)
            elif (isinstance(event, OpenTermEvent)):
                self.scheduler.add_job(topology.get_node_by_name(
                    event.node_name).open_term, 'date', run_date=self._calculate_new_time(event.execution_delay), args=event.args)
            else:
                raise ValueError(
                    "Event_type doesn't match any predefined event types")

    def start(self):
        '''
            Stars the schedulers and sets the is_started flag to true.
        '''
        self.is_started = True
        return self.scheduler.start()

    def get_jobs(self):
        '''
            Returns the jobs scheduled for execution
        '''
        return self.scheduler.get_jobs()

    def print_jobs(self):
        '''
        Prints a formatted version of the jobs scheduled for execution
        '''
        return self.scheduler.print_jobs()

    def format_job(self, job_id):
        '''
        Formats a job so that it can be shown to the user when an API call is made
        '''
        job = self.scheduler.get_jobs
        return self.format_jobs(job_id=job_id)

    def format_jobs(self, job_id=None):
        '''
        Formats all of the jobs so that they can be shown to the user when an API call is made
        '''
        jobs = []
        if (job_id == None):
            jobs = self.get_jobs()
        else:
            print("id " + job_id)
            jobs.append(self.scheduler.get_job(job_id))

        result = []
        c = 0
        for job in jobs:
            data = OrderedDict()
            data['number'] = str(c)
            c += 1
            data['runtime'] = str(job.next_run_time)
            data['id'] = str(job.id)
            data['name'] = str(job.name)
            data['function'] = str(job.func)
            data['args'] = str(job.args)
            data['kwargs'] = str(job.kwargs)
            result.append(data)
        return result

    def _calculate_new_time(self, delay):
        '''
        This method used to calculate a new date time object for the execution of an event.

        Since in the event config file a time value in second is provided, this must be converted to a datettime object.
        This is done by making note of the time when the scheduler is started, and adding that to the execution time of the event.
        This gives a new datetime object, which refers to the correct execution time.
        '''
        original_datetime = self.start_time
        delta = timedelta(seconds=float(delay))
        execution_datetime = original_datetime + delta
        return execution_datetime
