# What is it?

If you find AWS Cloudwatch logs a pain in the ass, and would like to download a log stream of a log group locally
and would rather tail on the log, this application will download the log file for you.   

# How do I run it?
Set up the configuration:

1. 
```
export AWS_ACCESS_KEY=xxxxxx
export AWS_SECRET_KEY=xxxxxx
export AWS_SESSION_TOKEN=xxxxxx 
export AWS_REGION=us-east-1
export LOG_GROUP_NAME=/ecs/<log group>  # log group to fetch
export CWL_ENV=<your env namespace> # defaults to dev
```

Optional env variables:

To configure the batch size (number of logs to be pulled per query, default 100)
```
export BATCH_SIZE=100
```  

To configure how many log streams to start pulling logs from (latest first)
defaults to 1

```
export STREAM_LOOKBACK_COUNT=1
```

```export MIXPANEL_TOKEN=xxxx``` if you want to report the log events to Mixpanel
```export AWS_LOGS_DIRECTORY=aws-logs``` if you want to write the log events to local file system



2. Run the [pex](https://pex.readthedocs.io/en/stable/) executable (you need pip3)
```
./build_and_run.sh
```

You should see the logs being downloaded under the `/var/log/cloudwatchlogs/<cwl group name>/<cwl stream name>` directory grouped by the log group directory and all the log streams desired under the directory as separate file(s)

# Logs
You can view the daemon logs at `cwl.log`


## Maintaining State
A state file (checkpoint) is maintained under the project directory named `cwl.state`. This file contains the last time the file was modified and a map of log stream to the last processed `nextToken` so if the process dies, it can read from the state and resume from that point.

## Monitoring
1. Monitor if the files are being written to with system leven information like total file size(s) etc. [TODO]
2. Monitor the daemon processes are alive or not. [DONE]
