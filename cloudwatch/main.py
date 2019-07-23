import json
import threading
import time
from threading import Lock
from cloudwatch.config import *
import boto3
from cloudwatch.cwl import CloudWatchLogs
from cloudwatch.consumer_mixpanel import MixpanelConsumer
from cloudwatch.consumer_filesystem import FileSystemConsumer
from cloudwatch.utils import create_file_if_does_not_exist

"""
GLOBALS GO HERE


the log stream map is a log stream discovery mechanism that lets the main process
know which threads are working on which log streams
Key: Tuple(log group name, log stream name), value: the thread id (optional for now)

Basically we want a set of the log streams currently being processed so that later they
can be reaped from this map when the thread is "Done" or more threads can be added to it
as we discover more log streams
"""
LOG_STREAM_MAP = {}
LOG_STREAM_CHECKPOINT = {}  # key = stream id, value = next token to be fetched

s3_client = boto3.client('s3')


class GlobalManager(object):
    """
    Helper class to set/get shared state and variables
    """

    def __init__(self):
        self.lock = Lock()

    def get_log_stream_map(self):

        self.lock.acquire()
        try:
            return LOG_STREAM_MAP
        finally:
            self.lock.release()

    def set_log_stream_map(self, key, value):
        self.lock.acquire()
        try:
            logging.info("setting the stream {} to thread {}".format(key, value))
            LOG_STREAM_MAP[key] = value
        finally:
            self.lock.release()

    def delete_stream_from_map(self, key):
        self.lock.acquire()
        try:
            if LOG_STREAM_MAP.get(key):
                del LOG_STREAM_MAP[key]
        finally:
            self.lock.release()

    def get_checkpoint(self):

        self.lock.acquire()
        try:
            return LOG_STREAM_CHECKPOINT
        finally:
            self.lock.release()

    def set_checkpoint(self, key, value):
        self.lock.acquire()
        try:
            LOG_STREAM_CHECKPOINT[key] = value
        finally:
            self.lock.release()


gb = GlobalManager()


class LogStreamHandler(object):

    def __init__(self, client):
        self.aws_client = client
        self.lock = Lock()

    def write_log(self, log_group_name, log_stream_name, consumers):
        """
        Writes the log to the log file
        @param file_name: The log file name to be written to
        @param log_group_name: The log group name
        @param log_stream_name: The log stream name
        @param consumers: List of consumers of type BaseConsumer
        """

        # get the data from the log group
        for _logs in self.aws_client.get_log_events(log_group_name, log_stream_name, gb):
            # handle the log events
            for _log in _logs:
                for consumer in consumers:
                    consumer.process(_log, log_group_name, log_stream_name)

    def _wanted_log_stream(self, log_stream_name):
        return True

    def _remove_old_streams(self, streams):
        """
        Removes any old streams from the LOG_STREAM_MAP
        """

        for stream in streams:
            if not gb.get_log_stream_map().get(LOG_GROUP_NAME, stream):
                logging.warning("CLEANING UP LOG STREAM: {}/{}".format(LOG_GROUP_NAME, stream))
                k = (LOG_GROUP_NAME, stream)
                gb.delete_stream_from_map(k)

    def _discover_log_streams(self):
        """
        This method is used by the main process to discover new log streams
        and keep a shared state(map) of the log streams being worked on.
        """
        log_streams = self.aws_client.get_log_streams(
            log_group_name=LOG_GROUP_NAME, stream_lookback_count=STREAM_LOOKBACK_COUNT)

        self._remove_old_streams(log_streams)

        for log_stream in log_streams:
            lsn = log_stream['logStreamName']
            if not gb.get_log_stream_map().get((LOG_GROUP_NAME, lsn)):
                # setting the value to None is an indication that no thread is working on the log stream
                if self._wanted_log_stream(lsn):
                    logging.info("Log stream {} not tracked - starting to track".format(lsn))
                    gb.set_log_stream_map((LOG_GROUP_NAME, lsn), None)
            else:
                logging.info("Stream {} already being processed".format(log_stream['logStreamName']))
        logging.info("Log stream map: {}".format(gb.get_log_stream_map()))

    def discover_log_streams(self):
        """
        A daemon that continuously looks for log streams
        """
        while True:
            self._discover_log_streams()
            time.sleep(TIME_DAEMON_SLEEP)

    def _get_new_log_streams(self):
        """
        Reads from the global log stream map to find any new streams that
        have not been handled. If so, return those
        """

        self.lock.acquire()

        new_streams = []
        logging.info("Stream map {}".format(gb.get_log_stream_map().items()))
        for key, value in gb.get_log_stream_map().items():
            if value is None:
                new_streams.append(key)
        if new_streams:
            logging.info("Found new Streams: %s", str(new_streams))

        self.lock.release()

        return new_streams

    def sync_new_logs(self):
        """
        Syncs the newly discovered log streams to the file system by starting off
        a thread that consumes those logs. Also marks the MAP for those streams as being processed
        """

        while True:

            new_streams = self._get_new_log_streams()

            self.lock.acquire()
            logging.info("New streams: {}".format(new_streams))

            if not new_streams:
                time.sleep(TIME_DAEMON_SLEEP)

            for log_group_name, log_stream_name in new_streams:
                log_getter = threading.Thread(
                    target=self.write_log, args=(log_group_name, log_stream_name, consumers))
                logging.info("Consuming log stream: %s, %s %s", log_group_name, log_stream_name, log_getter)
                gb.set_log_stream_map((log_group_name, log_stream_name), log_getter)
                log_getter.start()

            self.lock.release()

    def persist_state(self, location='cwl.state'):
        """
        Persist the checkpoint state in a specific location
        :param state: Dictionary of key = stream (id), value = next token  
        :param location: location of file. #TODO save to s3 or dynamo later
        """

        state = {}

        while True:
            state['modified_time'] = time.asctime()
            state.update(gb.get_checkpoint())
            state_json = json.dumps(state)
            create_file_if_does_not_exist(location)

            fhandle = open(location, 'w')
            # handle the log events
            fhandle.write(state_json)
            fhandle.flush()
            fhandle.close()

            # with open(location, 'rb') as data:
            #     s3_client.upload_fileobj(data, 'cloudwatch.mixpanel.state', "{}-state".format(CWL_ENV))
            time.sleep(1)


def configure_logging():
    """
    Configure the logging
    """
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        format=LOG_FORMAT
    )


class LogProcessMonitor(object):
    """
    Monitors the processes that write to the logs
    """

    def __init__(self):
        pass

    def log_status(self):
        """
        Logs the status of the processes
        @param log_stream_map: the global log stream map the main process uses to orchestrate threads
        """
        while True:
            for _log_group_stream, _processing_thread in gb.get_log_stream_map().items():
                logging.info(
                    "Log Group: {0}, Stream: {1} is processed by: {2}".format(
                        _log_group_stream[0], _log_group_stream[1], _processing_thread)
                )
            time.sleep(TIME_DAEMON_SLEEP)


def load_checkpoint():
    try:
        f = open('cwl.state', 'r')
        checkpoint = f.read()
        logging.info("checkpoint found")
        checkpoint = json.loads(checkpoint)
        logging.info("parsed checkpoint is %s", checkpoint)
        del checkpoint['modified_time']
        for key, value in checkpoint.items():
            gb.set_checkpoint(key, value)
    except Exception as ex:
        logging.warning("No checkpoint found {}".format(repr(ex)))


if __name__ == '__main__':
    try:

        configure_logging()
        client = CloudWatchLogs(AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_SESSION_TOKEN)

        logstreamhandler = LogStreamHandler(client)

        load_checkpoint()

        mp_consumer = MixpanelConsumer()
        fs_consumer = FileSystemConsumer()
        consumers = []
        if MIXPANEL_TOKEN:
            consumers.append(mp_consumer)
        if AWS_LOGS_DIRECTORY:
            consumers.append(fs_consumer)

        discover_log_streams_thread = threading.Thread(target=logstreamhandler.discover_log_streams, args=())

        logs_getter_thread = threading.Thread(target=logstreamhandler.sync_new_logs, args=())

        process_monitor_thread = threading.Thread(target=LogProcessMonitor().log_status, args=())

        persist_stream_checkpoint = threading.Thread(target=logstreamhandler.persist_state, args=())

        workers = [discover_log_streams_thread, logs_getter_thread, process_monitor_thread, persist_stream_checkpoint]

        logging.info("Log stream map %s", gb.get_log_stream_map())
        for worker in workers:
            worker.daemon = True
            worker.start()
        while True:
            logging.info("Heartbeat")
            time.sleep(TIME_DAEMON_SLEEP)

            # check the health of threads. restart if they have died and log loudly
            for worker in workers:
                if not worker.is_alive():
                    logging.exception(
                        "!! Worker thread {} died around time {} - restarting it.".format(worker.name, time.asctime())
                    )
                    worker.start()

    except KeyboardInterrupt as ex:
        logging.error("Keyboard interrupt received..")
