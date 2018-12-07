# What is it?

If you find AWS Cloudwatch logs a pain in the ass, and would like to download a log stream of a log group locally
and would rather tail on the log, this application will download the log file for you.   

# How do I run it?
Set up the configuration:

1. 
```
export AWS_ACCESS_KEY=xxxxxx
export AWS_SECRET_KEY=xxxxxx 
export LOG_GROUP_NAME=/ecs/<log group>  # log group to fetch
export LOG_STREAMS_FILTER=ecs/nrc-container/foo,ecs/nrc-container/bar  # a CSV list of log stream to download.
```


2. Run the [pex](https://pex.readthedocs.io/en/stable/) executable
```
./cloudwatchlogs.pex 
```

You should see the logs being downloaded under the `aws_logs` directory grouped by the log group directory and all the log streams desired under the directory as separate file(s)

# Logs
You can view the daemon logs at `cwl.log`


# Development

```
1. Install pip
2. pip install wheel
3. rm -rf ~/.pex/ && rm cloudwatchlogs.pex && rm cloudwatchlogs-1.0-py2-none-any.whl
4. pip wheel -w . . && pex -f $PWD cloudwatchlogs boto3 python-slugify -m cloudwatch.main -o cloudwatchlogs.pex
```

# Consumers
You can modify the consumers in the main.py file. TODO this needs to be part of the config

## Daemon(s)

* Will probably use multiprocess/threads [Discussion] to read the configuration and the log streams
* Listen to any new log events in those streams and write to the files

### Signal Handling
* On an interrupt (SIGINT etc.), the program should close any open file descriptors
* Since a daemon process doesn't get a SIGHUP from the kernel, we can use a SIGHUP handler to reload the configuration

## multiprocesses vs threads
* The batch size when writing to the files. One reason to use multiprocess instead of threads is that a single
process may have a max RLIMIT_*
* Because of Python's GIL, using multi-core processors is not possible. If anything, multi-cores make the processing slower.
* however threads are easy to use than processes if we need thread communication and global state

## Maintaining State
A state file (checkpoint) is maintained under the project directory named `cwl.state`. This file contains the last time the file was modified and a map of log stream to the last processed `nextToken` so if the process dies, it can read from the state and resume from that point.

## Monitoring
1. Monitor if the files are being written to with system leven information like total file size(s) etc. [TODO]
2. Monitor the daemon processes are alive or not. [DONE]
