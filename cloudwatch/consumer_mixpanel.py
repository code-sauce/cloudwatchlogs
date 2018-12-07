from cloudwatch.consumer_abstract import BaseConsumer
import json


class MixpanelConsumer(BaseConsumer):

    def process(self, log_line, log_group, log_stream):

        try:
            message = log_line['message']
            message = json.loads(message)
            message = message.get('message')
            message = json.loads(message)
            templatized_url = message.get('templatized_url')
            if not templatized_url:
                return
            app_id = message.get('app_id')

            # TODO - fire events to mixpanel
            print("firing {} and {} to mixpanel".format(templatized_url, app_id))
        except Exception as ex:
            pass
