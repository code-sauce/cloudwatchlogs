# What is it?

If you find AWS Cloudwatch logs a pain in the ass, and would like to download a log stream of a log group locally
and would rather tail on the log, this application will download the log file for you.   

# Setup and Running

Just run the [pex](https://pex.readthedocs.io/en/stable/) executable
```
./cloudwatchlogs.pex 
```

# Building
```
1. pip wheel -w . .
2. pex -f $PWD cwlogs boto3 python-slugify -m cloudwatch.main -o cloudwatchlogs.pex

```

## Daemon(s)

* Will probably use multiprocess/threads [Discussion] to read the configuration and the log streams
* Listen to any new log events in those streams and write to the files

### Signal Handling
* On an interrupt (SIGINT etc.), the program should close any open file descriptors
* Since a daemon process doesn't get a SIGHUP from the kernel, we can use a SIGHUP handler to reload the configuration


## Configuration
The configuration of the application includes:
* `AWS_ACCESS_KEY` and `AWS_SECRET` as environment variables
* `AWS_LOGS_DIRECTORY` - location of downloaded logs 
* `LOG_GROUP_NAME_PREFIX` - log group prefix to fetch
* `LOG_STREAMS_FILTER` - eg `['ecs/nrc-container/33fb88f0-2071-4bfa-96ed-abbc396172c4']` a list of log stream to download.

## multiprocesses vs threads
* The batch size when writing to the files. One reason to use multiprocess instead of threads is that a single
process may have a max RLIMIT_*
* Because of Python's GIL, using multi-core processors is not possible. If anything, multi-cores make the processing slower.
* however threads are easy to use than processes if we need thread communication and global state

## Maintaining State [TODO]
1. A state needs to be maintained when polling for logs.
Eg. if stream1 was being polled, we need to maintain which was the last log written [nextForwardToken]
so that if the daemon is interrupted or restarted, we can resume the process from where we last dropped off

## Monitoring
1. Monitor if the files are being written to with system leven information like total file size(s) etc. [TODO]
2. Monitor the daemon processes are alive or not. [DONE]
