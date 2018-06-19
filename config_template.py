import logging

AWS_ACCESS_KEY = ''
AWS_SECRET_KEY = ''
LOG_FILE = 'cwl.log'
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
AWS_LOGS_DIRECTORY = 'aws-logs'
TIME_DAEMON_SLEEP = 10  # seconds
TIME_LOG_POLL_SLEEP = 1

LOG_GROUP_NAME_PREFIX = '/ecs/nrc'
LOG_STREAMS_FILTER = ['ecs/nrc-container/d2624e46-3781-491e-83ab-693fed25a9e5']
