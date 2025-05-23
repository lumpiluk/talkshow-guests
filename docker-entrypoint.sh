#!/usr/bin/env sh

# Environment variables are not available to cron by default,
# so dump them to a file before starting cron:
printenv | grep -v "no_proxy" | sed 's/^/export /' > /etc/talkshowguests_env

# Start cron in the foreground
cron -f
