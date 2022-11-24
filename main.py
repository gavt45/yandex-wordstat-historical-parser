
import os

from yandex_parser import Parser

import logging

from yandex_parser.worker import Worker

logging.basicConfig(level=logging.INFO)



if __name__ == '__main__':
    if not os.path.exists('data/captcha'):
        os.mkdir("data")
        os.mkdir("data/captcha")

    parser = Parser(
        yandex_login=os.environ['EMAIL'],
        yandex_pass=os.environ['PASS'],
        webdriver_uri=os.environ['WEBDRIVER'],
        proxy_uri=os.environ['PROXY_URI'],
        rucaptcha_key=os.environ['RUCAPTCHA_TOKEN']
    )

    worker = Worker(
        host=os.environ['RHOST'],
        port=int(os.environ['RPORT']),
        parser=parser
    )

    try:
        parser.login_wordstat()

        worker.work()

        # d = pd.read_csv('queries.csv').drop(['Unnamed: 0'], axis=1)
        # d_grouped = pd.DataFrame()
        # col_first = list(d['brand_match'].value_counts().to_dict().keys())[6:]
        # col_last = list(d['brand_match'].value_counts().to_dict().keys())[:6]
        #
        # for i in col_first:
        #     d_grouped = pd.concat([d_grouped, d[d['brand_match'] == i]])
        # for i in col_last:
        #     d_grouped = pd.concat([d_grouped, d[d['brand_match'] == i]])
        #
        # d_grouped['parse_data'] = ''
        # last_idx = 0
        # for idx, row in d_grouped.iterrows():
        #     if idx < last_idx:
        #         continue
        #     data = parser.get(row.KEYWORD)
        #     d_grouped.at[idx, 'ws'] = str(data)
        #     last_idx += 1
        #     sleep(random() * 1)
    except Exception as e:
        parser.close()
        raise e
    except KeyboardInterrupt as e:
        parser.close()
        raise e