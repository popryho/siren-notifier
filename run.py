import argparse
import asyncio
import hashlib
import imghdr
import json
import logging
import os
import random

import imagehash
from PIL import Image
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDhConfigRequest
from telethon.tl.functions.phone import RequestCallRequest
from telethon.tl.types import PhoneCallProtocol

logging.basicConfig(
    filename="logs.log",
    filemode='a',
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO
)


def get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--dial_usernames", type=str, nargs='+', default=["@username1", "@username2"], required=True,
                        help="telegram usernames of the users you want to notify")
    parser.add_argument("--url_to_channel", type=str, default="https://t.me/khm_gov_ua", required=True,
                        help="url to the channel where important messages are posted")
    return parser


async def dial_numbers(client: TelegramClient, usernames_list: list):
    """Call one or more users using telegram calls."""

    async def get_dh_config():
        class DH:
            def __init__(self, dh_config):
                self.p = int.from_bytes(dh_config.p, 'big')
                self.g = dh_config.g
                self.resp = dh_config

        return DH(await client(GetDhConfigRequest(version=0, random_length=256)))

    dh_config = await get_dh_config()

    def get_rand_bytes(length=256):
        return bytes(x ^ y for x, y in zip(
            os.urandom(length), dh_config.resp.random
        ))

    def integer_to_bytes(integer):
        return int.to_bytes(
            integer,
            length=(integer.bit_length() + 8 - 1) // 8,  # 8 bits per byte,
            byteorder='big',
            signed=False
        )

    async def call_user(input_user):
        PROTOCOL = PhoneCallProtocol(
            min_layer=93, max_layer=93, udp_p2p=True, library_versions=['1.24.0'])
        dhc = await get_dh_config()

        a = 0
        while not (1 < a < dhc.p - 1):
            # "A chooses a random value of a, 1 < a < p-1"
            a = int.from_bytes(get_rand_bytes(), 'little')

        g_a = pow(dhc.g, a, dhc.p)

        await client(RequestCallRequest(
            user_id=await client.get_entity(input_user),
            random_id=random.randint(0, 0x7fffffff - 1),
            g_a_hash=hashlib.sha256(integer_to_bytes(g_a)).digest(),
            protocol=PROTOCOL)
        )

    for username in usernames_list:
        logging.info(f"Dialing {username}")
        await call_user(username)


def are_two_images_equal(
        first_image: Image, second_image: Image, cutoff: int) -> bool:
    """
    param: cutoff: the maximum bits that could be different between the hashes.
    The hash (or fingerprint) is derived from a 8x8 monochrome thumbnail of the image.
    """
    first_hash = imagehash.average_hash(first_image)
    second_hash = imagehash.average_hash(second_image)

    return abs(first_hash - second_hash) < cutoff


async def work(client):
    async with client:

        args = get_parser().parse_args()
        channel_entity = await client.get_entity(args.url_to_channel)
        await client(JoinChannelRequest(channel_entity))

        alarm_on = Image.open('alarm_on.jpg')
        alarm_off = Image.open('alarm_off.jpg')

        @client.on(events.NewMessage(chats=channel_entity))
        async def handler(event):
            await event.download_media('temp.jpg')
            
            if not imghdr.what('temp.jpg') == 'jpeg':
                logging.info(f"file type is: {imghdr.what('temp.jpg')}")
                return
            img: Image = Image.open('temp.jpg')

            if are_two_images_equal(alarm_on, img, cutoff=5):
                logging.info("ALARM ON")
                await dial_numbers(client, args.dial_usernames)
            elif are_two_images_equal(alarm_off, img, cutoff=5):
                logging.info("ALARM OFF")
                await dial_numbers(client, args.dial_usernames)

        await client.run_until_disconnected()


async def main():

    try:
        with open("session.conf") as f:
            conf = json.load(f)
            api_id = conf['api_id']
            api_hash = conf['api_hash']
            session_name = conf['session_name']
    except Exception as e:
        logging.info(f"Failed to load session.conf: {repr(e)}")
        quit()

    await work(TelegramClient(session_name, api_id, api_hash))

asyncio.run(main())
