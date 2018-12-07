class BaseConsumer(object):
    """
    This class sets the blueprint for all the log event consumers
    """

    @staticmethod
    def process(log_line, log_group, log_stream):
        pass
