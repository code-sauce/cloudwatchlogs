#!/usr/bin/env bash
pip3 install wheel
pip3 install pex
rm -rf ~/.pex/ && rm cloudwatchlogs.pex && rm cloudwatchlogs-1.0-py2-none-any.whl
pip3 wheel -w . . && pex -f $PWD cloudwatchlogs mixpanel boto3 python-slugify -m cloudwatch.main -o cloudwatchlogs.pex
./cloudwatchlogs.pex
