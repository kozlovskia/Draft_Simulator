import time
import requests
from pathlib import Path

import pandas as pd
import numpy as np


def get_summoners(api_key, region, tier, division, queue='RANKED_SOLO_5x5', df_path='data/summoners.csv'):

    if not Path(df_path).exists():
        out_df = pd.DataFrame(columns=['region', 'leagueId', 'queueType', 'tier', 'rank', 'summonerId', 'summonerName'])
    else:
        out_df = pd.read_csv(df_path)

    out_dict = {'region': [], 'leagueId': [], 'queueType': [], 'tier': [],
                'rank': [], 'summonerId': [], 'summonerName': []}
    i = 1
    while True:

        URL = 'https://' + region + '.api.riotgames.com/lol/league/v4/entries/' \
              + queue + '/' + tier + '/' + division + '/?page=' + str(i) + '&api_key=' + api_key

        response = requests.get(URL)
        while response.status_code != 200:
            time.sleep(2)
            print(f"Can't get response...waiting | status code: {response.status_code}")
            response = requests.get(URL)
        response_json = response.json()
        if len(response_json) == 0:
            break
        for summoner in response_json:
            out_dict['region'].append(region)
            for k in out_dict.keys():
                if k == 'region':
                    continue
                out_dict[k].append(summoner[k])

        print(f'Region: {region} | Tier: {tier} {division} | Page: {i}...')
        i += 1

    out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
    out_df.to_csv('data/summoners.csv', index=False)


if __name__ == '__main__':
    api_key = 'RGAPI-178a46d7-fc23-4307-912f-5477ac30cfa5'
    regions = ['eun1', 'euw1', 'kr', 'na1']
    divisions = ['I', 'II', 'III', 'IV']

    for region in regions:
        for div in divisions:
            get_summoners(api_key, region, 'DIAMOND', div)
