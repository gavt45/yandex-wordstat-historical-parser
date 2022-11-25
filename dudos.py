import redis
from time import sleep
import pandas as pd
import os
import json

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

    process_data = data.loc[start_idx:start_idx + 2]
    keywords_idx = set(process_data['index'].to_list())

    for idx, row in process_data.iterrows():
        enqueue(row['index'], row['KEYWORDS'])

    res_dict = {}
    while len(keywords_idx):
        d = c.rpop("done")
        if d:
            result = json.loads(d.decode('utf-8'))
            print(result['uid'], keywords_idx)

            if 'dataGroups' not in result['data']:
                res_dict[result['uid']] = {}
            else:
                res_dict[result['uid']] = result['data']['dataGroups'][0]

            keywords_idx.remove(int(result['uid']))
        sleep(1)
        if not c.llen("tasks") and len(keywords_idx) != 0:
            for idx in list(keywords_idx):
                enqueue(idx, process_data[process_data['index'] == idx]['KEYWORDS'][idx])

    with open(f'res/{start_idx + 2}.json', 'w') as fp:
        json.dump(res_dict, fp)




