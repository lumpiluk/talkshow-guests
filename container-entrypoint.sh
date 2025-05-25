#!/usr/bin/env bash

set -euo pipefail
IFS=$'\n\t'

# Use existing UID/GID from mounted /data directory:
HOST_UID=$(stat -c '%u' /data)
HOST_GID=$(stat -c '%g' /data)

user_exists(){ id "$1" &>/dev/null; }

if [ "$HOST_UID" -ne 0 ]; then
    if ! user_exists hostuser; then
        addgroup --gid $HOST_GID hostgroup
        adduser --uid $HOST_UID \
            --gid $HOST_GID \
            --disabled-password \
            --no-create-home \
            --gecos "" \
            hostuser
    fi
    CRON_USER=hostuser
    echo "Running with UID $HOST_UID based on ownership of the /data directory."
else
    echo "Running as root based on ownership of the /data directory."
    CRON_USER=root
fi

default_schedule='*/20 * * * *'
CRAWL_SCHEDULE="${CRAWL_SCHEDULE:-$default_schedule}"
echo "Will crawl talkshows using this schedule: $CRAWL_SCHEDULE"

echo "$CRAWL_SCHEDULE $CRON_USER /run.sh >> /var/log/cron.log 2>&1" \
    > /etc/cron.d/talkshowguests
chmod 0644 /etc/cron.d/talkshowguests
touch /var/log/cron.log
chown "$CRON_USER":"$HOST_GID" /var/log/cron.log

# Environment variables are not available to cron by default,
# so dump them to a file before starting cron:
printenv | grep -v "no_proxy" | sed 's/^/export /' > /etc/talkshowguests_env

# Start cron in the foreground
# (as root; hostuser is specified in the cron job)
cron -f
