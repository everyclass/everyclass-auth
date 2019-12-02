import asyncio
import json
import re
import time
import uuid

from everyclass.auth.db.postgres import init_pool
from everyclass.auth.email_verification import handle_email_register_request
from everyclass.auth.message_queue import RedisQueue
from everyclass.auth.password_verification import handle_browser_register_request


def expensive_task(arg1):
    print("i am expensive and i will go")
    raise RuntimeError("boom")
    time.sleep(10)
    print("ok i'm done")


async def async_handle_browser_register_request(request_id, username, password):
    try:
        await loop.run_in_executor(None, handle_browser_register_request,
                                   request_id,
                                   username,
                                   password)
    except Exception as e:
        print("Exception raised while executing browser request: %s" % repr(e))
        raise


async def async_handle_email_register_request(request_id, username):
    try:
        await loop.run_in_executor(None, handle_email_register_request,
                                   request_id,
                                   username)
    except Exception as e:
        print("Exception raised while executing email request: %s" % repr(e))
        raise


async def check():
    print("Start main task")
    init_pool()
    user_queue = RedisQueue("everyclass")
    while True:
        # user_queue.put({"request_id": str(uuid.uuid4()),
        #                 "username"  : "fake-3901160407",
        #                 "method"    : "password",
        #                 "password"  : "test"})
        result = user_queue.get_wait()[1]  # block main thread
        if not result:
            continue
        request_info = bytes.decode(result)
        request_info = re.sub('\'', '\"', request_info)
        request_info = json.loads(request_info)

        if request_info['method'] == 'password':
            print("Async task (password) spawned")
            asyncio.ensure_future(async_handle_browser_register_request(request_info['request_id'],
                                                                        request_info['username'],
                                                                        request_info['password']))
        elif request_info['method'] == 'email':
            print("Async task (email) spawned")
            asyncio.ensure_future(async_handle_email_register_request(request_info['request_id'],
                                                                      request_info['username']))
        await asyncio.sleep(1)
        print("loop end")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([asyncio.ensure_future(check())]))
