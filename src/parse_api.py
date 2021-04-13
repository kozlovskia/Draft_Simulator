import time
import requests
from pathlib import Path
from multiprocessing import Process

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
    out_df.to_csv(df_path, index=False)


def separate_summoners(regs, summoners_csv_path='data/summoners.csv'):

    df = pd.read_csv(summoners_csv_path)
    for reg in regs:
        reg_df = df.loc[df['region'] == reg]
        reg_df.to_csv(f'{summoners_csv_path[:-4]}_{reg}.csv', index=False)


def get_accounts(api_key, region, out_df_path, summoners_csv_path):

    if not Path(out_df_path).exists():
        out_df = pd.DataFrame(columns=['region', 'summonerId', 'accountId'])
    else:
        out_df = pd.read_csv(out_df_path)

    df = pd.read_csv(summoners_csv_path)
    region_df = df.loc[df['region'] == region]
    out_dict = {'region': [], 'summonerId': [], 'accountId': []}

    for i, row in region_df.iterrows():

        reg = row['region']
        summoner_id = row['summonerId']
        URL = 'https://' + reg + '.api.riotgames.com/lol/summoner/v4/summoners/' \
              + summoner_id + '?api_key=' + api_key

        response = requests.get(URL)
        while response.status_code != 200:
            time.sleep(5)
            print(f"Region: {region} | Can't get response...waiting | status code: {response.status_code}")
            response = requests.get(URL)
        response_json = response.json()
        if len(response_json) == 0:
            break

        out_dict['region'].append(reg)
        out_dict['summonerId'].append(summoner_id)
        out_dict['accountId'].append(response_json['accountId'])

        if i % 100 == 0 and i != 0:
            out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
            out_df.to_csv(out_df_path, index=False)
            print(f'Region: {region} | Checkpoint {i}...')
            out_dict = {'region': [], 'summonerId': [], 'accountId': []}

        print(f'Region: {region} | Processed {i}...')


if __name__ == '__main__':
    api_key = 'RGAPI-f9ca1cce-f572-442d-8f6c-71322ddc5d44'
    regions = ['eun1', 'euw1', 'kr', 'na1']
    divisions = ['I', 'II', 'III', 'IV']

    # for region in regions:
    #     for div in divisions:
    #         get_summoners(api_key, region, 'DIAMOND', div)
    # separate_summoners(regions)

    processes = []
    for region in regions:
        processes.append(Process(target=get_accounts, args=(api_key, region, f'data/accounts_{region}.csv',
                                                            f'data/summoners_{region}.csv')))

    for p in processes:
        p.start()
    for p in processes:
        p.join()
