from cloudwatch.consumer_abstract import BaseConsumer
from slugify import slugify
from cloudwatch.utils import create_file_if_does_not_exist
from cloudwatch.config import *


class FileSystemConsumer(BaseConsumer):

    @staticmethod
    def _get_log_dir_name(log_group_name):
        return slugify(log_group_name)

    @staticmethod
    def _get_file_name(log_group_name, log_stream_name):
        """
        Given a log group and a log stream name, generates the sanitized
        file name to be written to. Cleans any special characters
        @param log_group_name: The log group name
        @param log_stream_name: The log stream name
        """

        sanitized_log_group_name = FileSystemConsumer._get_log_dir_name(log_group_name)
        sanitized_log_stream_name = slugify(log_stream_name)
        dir_path = os.path.join(AWS_LOGS_DIRECTORY, sanitized_log_group_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return "{0}/{1}/{2}.log".format(
            AWS_LOGS_DIRECTORY, sanitized_log_group_name, sanitized_log_stream_name)

    @staticmethod
    def process(log_line, log_group, log_stream):
        file_name = FileSystemConsumer._get_file_name(log_group, log_stream)
        create_file_if_does_not_exist(file_name)
        fhandle = open(file_name, 'a+')
        print("RAW LOG LINE: ", log_line)
        fhandle.write(str(log_line) + '\n')
        fhandle.flush()
        fhandle.close()

