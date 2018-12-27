import logging
import os

AWS_ACCESS_KEY = os.environ['AWS_ACCESS_KEY']
AWS_SECRET_KEY = os.environ['AWS_SECRET_KEY']

LOG_FILE = 'cwl.log'
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

TIME_DAEMON_SLEEP = 10  # seconds
TIME_LOG_POLL_SLEEP = 4

LOG_GROUP_NAME = os.environ['LOG_GROUP_NAME']
LOG_STREAMS_FILTER = None
try:
    LOG_STREAMS_FILTER = os.environ['LOG_STREAMS_FILTER'].split(',')
except:
    print("No specific log streams to be downloaded")
    logging.exception("No specific log streams to be downloaded")
BATCH_SIZE = os.environ.get('BATCH_SIZE') or 1000
STREAM_LOOKBACK_COUNT = 1

# Consumption
MIXPANEL_TOKEN = os.environ.get("MIXPANEL_TOKEN")
AWS_LOGS_DIRECTORY = os.environ.get("AWS_LOGS_DIRECTORY")  # if you want to write the logs to local file system
CWL_ENV = os.environ.get('CWL_ENV') or "dev"
