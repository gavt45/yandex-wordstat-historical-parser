import logging

import redis
import json
from time import sleep


class Worker:
    TASKS_EXC = "tasks"
    DONE_EXC = "done"

    def __init__(self,
                 host,
                port,
                 parser
            ):
        self.r = redis.Redis(host=host, port=port)
        self.ps = self.r.pubsub()
        self.ps.subscribe(self.TASKS_EXC)
        self.parser = parser
        self.done = False

    def load(self, msg: str):
        try:
            m = json.loads(msg)
            return m['uid'], m['kw'], m['cmd']
        except json.decoder.JSONDecodeError:
            return None, None, None
        except KeyError:
            return None, None, None

    def dump(self, uid, res: dict):
        return json.dumps({
                "uid": uid,
                "data": res
             })

    def work(self):
        while not self.done:
            dat = self.r.rpop(self.TASKS_EXC)
            if not dat:
                sleep(0.1)
                continue
            try:
                uid, kw, cmd = self.load(dat)
                logging.warn(f"[worker] Working: {uid} kw: {kw}")
                if not uid:
                    logging.warn(f"Strange msg: {dat}")
                    continue

                if cmd == 'exit':
                    self.done = True
                    self.parser.close()
                    continue

                data = self.parser.get(kw)

                if not data:
                    logging.warn("Return empty result!")
                    data = {}
                self.r.lpush(self.DONE_EXC, self.dump(uid, data))
            except Exception as e:
                self.parser.close()
                raise e
            except KeyboardInterrupt as e:
                self.parser.close()
                self.done = True
                raise e

if __name__ == "__main__":
    class ParserMock:
        def get(self, kw):
            return {"kw": kw}
        def close(self):
            logging.warn("parser EXIT!")
    worker = Worker(
        host="localhost",
        port=6379,
        parser=ParserMock()
    )
    worker.work()