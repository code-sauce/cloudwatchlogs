from cloudwatchlogs import CloudWatchLogs

client = CloudWatchLogs('AKIAJZ3AVWALC7UHJEFA', '9AiltquCqXjudirX1czm5L4gI8b3FUlGgaWKgmxe')
print client.get_log_groups()

print client.get_log_streams('RDSOSMetrics')

# print "GETTING EVENTS....."
# for event in  client.get_log_events('RDSOSMetrics', 'db-2R6ZW25HGYBFTXPN6LO7TW7O74'):
#     print event
