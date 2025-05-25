# Talkshow Guests

This project crawls the websites of several German talkshows and reports on future episodes and guest lists.

Talkshows on German national TV tend to announce their guests at most one day before a new live episode airs.
To the best of my knowledge there is no central public space where these future guests are published.
That's where this project comes in.

## Installation

First of all, clone this repository.

As of now, only reporting via a [Telegram bot](https://core.telegram.org/bots) is supported.
Create a new bot by messaging @BotFather.
Then store your API token in a new `.env` file (**Never commit or publish this file!**):

```
TELEGRAM_API_TOKEN=yourtokenhere
```

Create a new Telegram channel for the bot to post updates to and add your bot as an admin.
You will need to figure out the chat ID of your channel, so the bot can know where to post new updates.
You can do so by running
```bash
curl https://api.telegram.org/bot<YOUR API TOKEN HERE>/getUpdates
# example: https://api.telegram.org/bot123456789:ABCDEFG-HIJKLMN/getUpdates
```
If you don't see much in the output, remove and add your bot to the channel again, then re-run the command above.

Store this chat ID in your .env file as well:
```
TELEGRAM_API_TOKEN=yourtokenhere
TELEGRAM_CHAT_ID=yourchatid
```

### Docker

```bash
docker compose up -d
```

This will run the `talkshowguests` command in a cron job in the interval defined in `compose.yaml`.
This will crawl all supported web pages.
Crawl results are saved to `latest-results.jsonlines`.
If any new episodes were found that the bot hasn't reported on yet,
the bot will post a new update.
Finally, this will store a `history.json` that contains all previously reported episodes.

The files
`latest-results.jsonlines` and `history.json` will be written to the `data/` folder.

To check the cron.log file:
```bash
docker compose up -d
docker exec -it talkshowguests /bin/bash
$ cat /var/log/cron.log
```

#### Updating

```bash
docker compose down
docker compose up --build -d
```

### Poetry

Install Python and Poetry, then:

```bash
poetry install
poetry run talkshowguests --report-telegram
```

This will crawl all supported web pages.
Crawl results are saved to `latest-results.jsonlines`.
If any new episodes were found that the bot hasn't reported on yet,
the bot will post a new update.
Finally, this will store a `history.json` that contains all previously reported episodes.

You can also check the output of individual Spiders by running
```bash
poetry run scrapy crawl <name of spider>

# For example:
poetry run scrapy crawl carenmiosga
```
Check the [Scrapy documentation](https://docs.scrapy.org/en/latest/) for more details.
