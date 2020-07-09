import pysher
import logging
import time
import requests
import boto3
from dotenv import load_dotenv
import os


logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger(__name__)


def query_pool_public():
    timestamp = int(time.time() * 1000)
    resp = requests.get(f"https://cellbadge.com/com/cellbadge/client/siteProxy.cfc?method=getStatus&siteid={os.getenv('SITE_ID')}&_={timestamp}")
    return resp.json().get("STATUS", "")


def generate_template(status):
    html_begin = """<html>
<head>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
</head>
<body>"""
    html_end = """</body>
</html>"""

    return f"{html_begin}{status}{html_end}"


def generate_pool_html():
    try:
        pool_data = generate_template(query_pool_public())
    except Exception:
        log.exception("Error retrieving status")
        return False

    with open("pool.html", "wb") as fp:
        fp.write(pool_data.encode('utf8'))

    return True


def upload_badge_s3():
    if generate_pool_html():
        session = boto3.Session()
        s3_client = session.client('s3')
        s3_client.upload_file("pool.html", os.getenv("AWS_S3_BUCKET_NAME"), "pool.html",
                              ExtraArgs={'ContentType': "text/html", 'ACL': "public-read",
                                         'CacheControl': 'no-cache'})
        log.info("Successfully uploaded pool.html")


class PusherClass:
    def __init__(self):
        self.api_key = os.getenv("PUSHER_API_KEY")
        self.topic = f"dashboard_{os.getenv('SITE_ID')}"

        self.pusher = pysher.Pusher(self.api_key)
        self.pusher.connection.bind('pusher:connection_established', self.connect_handler)

    def connect_handler(self, data):
        # update the state any time we have to reconnect
        upload_badge_s3()
        channel = self.pusher.subscribe(self.topic)
        channel.bind('member_change', self.cb)

    def cb(self, *args, **kwargs):
        upload_badge_s3()

    def run(self):
        self.pusher.connect()


def main():
    p = PusherClass()
    p.run()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    load_dotenv()
    main()
