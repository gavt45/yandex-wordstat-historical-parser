from functools import reduce
import redis
from time import sleep
import pandas as pd
import os
import json
import logging
import datetime
import operator

logging.basicConfig(level=logging.INFO)

c = redis.Redis()

enqueue = lambda i, x: c.lpush("tasks", "{\"uid\":\"" + str(i) + "\", \"cmd\":\"\", \"kw\":\"" + x + "\"}")


def start_iter_value():
    results = os.listdir("res/")
    if not len(results):
        return 0
    for i in range(len(results)):
        results[i] = int(results[i].split('.')[0])
    return max(results)


if __name__ == "__main__":
    data = pd.read_csv('cosmetics_19k_sample.csv')
    start_idx = start_iter_value()

    process_data = data.loc[start_idx:start_idx + 1000]
    keywords_idx = set(process_data['index'].to_list())

    for idx, row in process_data.iterrows():
        enqueue(row['index'], row['KEYWORDS'])

    res_dict = {}
    distance_time = []
    request_time = datetime.datetime.now()
    epoch_time = datetime.datetime(1970, 1, 1)
    try:
        while len(keywords_idx):
            d = c.rpop("done")
            if d:
                if len(keywords_idx) % 20 == 0:
                    logging.info(f'Left {len(keywords_idx)} keywords')
                if len(distance_time) > 20:
                    td = reduce(operator.add, distance_time)
                    logging.info(f'Average time: {td.total_seconds() / len(distance_time)}')
                    distance_time.pop()
                if len(keywords_idx) % 100 == 0:
                    with open(f'res/{start_idx + 1000}.json', 'w') as fp:
                        json.dump(res_dict, fp)
                new_time = datetime.datetime.now()
                distance_time.append(new_time - request_time)
                request_time = new_time

                result = json.loads(d.decode('utf-8'))
                logging.info(f"Got {result['uid']} left: {len(keywords_idx)}")

                if 'dataGroups' not in result['data']:
                    res_dict[result['uid']] = {}
                else:
                    res_dict[result['uid']] = result['data']['dataGroups'][0]

                keywords_idx.remove(int(result['uid']))
            sleep(.01)
            if not c.llen("tasks") and len(keywords_idx) != 0:
                for idx in list(keywords_idx):
                    enqueue(idx, process_data[process_data['index'] == idx]['KEYWORDS'][idx])

        with open(f'res/{start_idx + 1000}.json', 'w') as fp:
            json.dump(res_dict, fp)

    except Exception as e:
        print(e)
        with open(f'res/{start_idx + len(list(res_dict.keys()))}_failed.json', 'w') as fp:
            json.dump(res_dict, fp)
    except KeyboardInterrupt:
        with open(f'res/{start_idx + len(list(res_dict.keys()))}_interrupted.json', 'w') as fp:
            json.dump(res_dict, fp)





