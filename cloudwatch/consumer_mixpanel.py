from cloudwatch.consumer_abstract import BaseConsumer


class MixpanelConsumer(BaseConsumer):

    def process(self, log_line, log_group, log_stream):
        print("MIXPANELLLLL")
        print(log_line)
        print(type(log_line))
