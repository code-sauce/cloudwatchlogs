"""
Module to interact with the cloudwatch logs
"""
import time
import logging

import boto3
seen_tokens = set()
from threading import Lock


from cloudwatch.config import *


class CloudWatchLogs(object):

    @staticmethod
    def _get_client(aws_access_key, aws_secret_key, aws_region, aws_session_token):
        return boto3.client(
            'logs',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            aws_session_token=aws_session_token
        )

    def __init__(self, aws_access_key, aws_secret_key, aws_region, aws_session_token):
        # injecting the AWS connection dependency
        if not (aws_access_key and aws_secret_key):
            raise Exception("Needs an AWS Connection string")
        self.client = CloudWatchLogs._get_client(aws_access_key, aws_secret_key, aws_region, aws_session_token)
        self.start_time = int(time.time()) * 1000
        self.lock = Lock()

        logging.info("Getting logs from time: {}".format(self.start_time))

    def get_log_groups(self, log_group_name_prefix=None):
        """
        For a given AWS cloudwatch connection, gets the CloudWatch Log Groups
        """
        log_groups = []
        next_token = ''
        while True:
            if not next_token:
                # first attempt
                response = self.client.describe_log_groups(logGroupNamePrefix=log_group_name_prefix)
            else:
                response = self.client.describe_log_groups(logGroupNamePrefix=log_group_name_prefix,
                                                           nextToken=next_token)
            logging.info("Log groups for prefix {}: {}".format(log_group_name_prefix, response['logGroups']))
            log_groups.extend(response['logGroups'])
            next_token = response.get('nextToken')
            if not next_token:
                break  # nothing more to fetch
        return log_groups

    def get_log_streams(self, log_group_name=None, stream_lookback_count=2):
        """
        Given a log group name, return the log streams
        @param log_group_name: Name of the log group
        @:param stream_lookback_count: Number of streams to lookback (descending sorted)
        returns: log streams[list] in the group
        """

        next_token = ''
        log_streams = []

        while True:
            if not next_token:
                # first attempt
                response = self.client.describe_log_streams(
                    logGroupName=log_group_name

                )
            else:
                response = self.client.describe_log_streams(
                    logGroupName=log_group_name,
                    nextToken=next_token
                )
            log_streams.extend(response['logStreams'])
            next_token = response.get('nextToken')
            if not next_token:
                break  # nothing more to fetch

        log_streams = sorted(log_streams, key=lambda x: x.get('lastEventTimestamp', float('-inf')), reverse=True)  # sort by event time desc
        return log_streams[:stream_lookback_count]  # only the latest streams

    def get_log_events(self, log_group_name, log_stream_name, gb, batch_limit=BATCH_SIZE, poll_sleep_time=6):
        """
        Gets the log events for the log group and log stream combination
        @param log_group_name: the log group name
        @param log_stream_name: the log stream in the group
        @param gb: global manager object to get/set globals
        @param batch_limit: the max number of log events returned
        @param poll_sleep_time: time to sleep (in seconds) between polling for logs, to avoid rate limit
        returns: log events [list]
        """

        # TODO: get only the logs from the starting time of the app. maybe maintain the state later

        next_token = ''
        log_events = []
        try:
            while True:
                self.lock.acquire()

                next_token = gb.get_checkpoint().get(log_stream_name) or ""

                # if next_token in seen_tokens:
                #     raise Exception("next token {} already seen".format(next_token))
                # seen_tokens.add(next_token)

                if not next_token:
                    # first attempt, try to load the checkpoint and find the next token
                    response = self.client.get_log_events(
                        logGroupName=log_group_name,
                        logStreamName=log_stream_name,
                        startFromHead=False,
                        limit=batch_limit
                    )
                else:
                    response = self.client.get_log_events(
                        logGroupName=log_group_name,
                        logStreamName=log_stream_name,
                        nextToken=next_token,
                        startFromHead=False,
                        limit=batch_limit
                    )

                next_forward_token = response['nextForwardToken']

                gb.set_checkpoint(log_stream_name, next_forward_token)

                self.lock.release()

                yield response['events']
                time.sleep(poll_sleep_time)

                if not next_forward_token:
                    break

        except Exception as ex:
            logging.exception(ex)
            # reraising
            raise ex
