import time
import requests
from pathlib import Path
from multiprocessing import Process
import json

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


def get_accounts(api_key, region, out_df_path, summoners_csv_path, start=0):

    if not Path(out_df_path).exists():
        out_df = pd.DataFrame(columns=['region', 'summonerId', 'accountId'])
    else:
        out_df = pd.read_csv(out_df_path)

    df = pd.read_csv(summoners_csv_path)
    region_df = df.loc[df['region'] == region]
    out_dict = {'region': [], 'summonerId': [], 'accountId': []}

    for i, row in region_df.iterrows():

        if i < start:
            continue

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

    out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
    out_df.to_csv(out_df_path, index=False)


def get_match_ids(api_key, region, out_df_path, accounts_csv_path, start=0):

    if not Path(out_df_path).exists():
        out_df = pd.DataFrame(columns=['region', 'queue', 'gameId'])
    else:
        out_df = pd.read_csv(out_df_path)

    df = pd.read_csv(accounts_csv_path)
    out_dict = {'region': [], 'queue': [], 'gameId': []}

    for i, row in df.iterrows():

        if i < start:
            continue

        reg = row['region']
        account_id = row['accountId']
        URL = 'https://' + reg + '.api.riotgames.com/lol/match/v4/matchlists/by-account/' \
              + account_id + '?api_key=' + api_key

        response = requests.get(URL)
        while response.status_code != 200:
            time.sleep(5)
            print(f"Region: {region} | Can't get response...waiting | status code: {response.status_code}")
            response = requests.get(URL)
        response_json = response.json()
        if len(response_json) == 0:
            break

        for game in response_json['matches']:
            if game['queue'] == 420 and game['season'] == 13:  # filtering only 2021 season soloq ranked games
                out_dict['region'].append(reg)
                out_dict['queue'].append(game['queue'])
                out_dict['gameId'].append(game['gameId'])

        if i % 100 == 0 and i != 0:
            out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
            out_df.to_csv(out_df_path, index=False)
            print(f'Region: {region} | Checkpoint {i}...')
            out_dict = {'region': [], 'queue': [], 'gameId': []}

        print(f'Region: {region} | Processed {i}...')

    out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
    out_df.to_csv(out_df_path, index=False)


def drop_duplicates(region, matchids_csv_path):

    t0 = time.time()
    matchids_df = pd.read_csv(matchids_csv_path)
    out_df = matchids_df.drop_duplicates(subset=['gameId'])

    out_df.to_csv(f'data/matchids_nodup_{region}.csv', index=False)
    print(f'Processed {region} in {round(time.time() - t0, 2)} sec(s)...')


def get_matches(api_key, region, out_df_path, matchids_csv_path, start=0):

    columns = ['platformId', 'queueId', 'gameId', 'gameVersion', 'winner']
    for i in range(1, 11):
        columns.append(f'participant_{i}_team')
        columns.append(f'participant_{i}_champ')

    if not Path(out_df_path).exists():
        out_df = pd.DataFrame(columns=columns)
    else:
        out_df = pd.read_csv(out_df_path)

    df = pd.read_csv(matchids_csv_path)
    out_dict = {column: [] for column in columns}

    for i, row in df.iterrows():

        if i < start:
            continue

        reg = row['region']
        game_id = row['gameId']
        URL = 'https://' + reg + '.api.riotgames.com/lol/match/v4/matches/' + str(game_id) + '?api_key=' + api_key

        response = requests.get(URL)
        if response.status_code == 404:
            print(f"Region: {region} | Error | status code: {response.status_code}")
            continue
        while response.status_code != 200:
            time.sleep(5)
            print(f"Region: {region} | Can't get response...waiting | status code: {response.status_code}")
            response = requests.get(URL)
        response_json = response.json()
        if len(response_json) == 0:
            break

        if not response_json['gameVersion'].startswith('11.'):  # filter games that were played before S2021
            continue

        out_dict['platformId'].append(response_json['platformId'])
        out_dict['queueId'].append(response_json['queueId'])
        out_dict['gameId'].append(response_json['gameId'])
        out_dict['gameVersion'].append(response_json['gameVersion'])
        winner = np.nan
        for team in response_json['teams']:
            if team['win'] == 'Win':
                winner = team['teamId']
        out_dict['winner'].append(winner)

        for participant in response_json['participants']:
            participant_id = participant['participantId']
            out_dict[f'participant_{participant_id}_team'].append(participant['teamId'])
            out_dict[f'participant_{participant_id}_champ'].append(participant['championId'])

        if i % 100 == 0 and i != 0:
            out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
            out_df.to_csv(out_df_path, index=False)
            print(f'Region: {region} | Checkpoint {i}...')
            out_dict = {column: [] for column in columns}
            with open('utils/checkpoints.json', 'r') as f:
                checkpoints = json.load(f)
                checkpoints[region] = i
            with open('utils/checkpoints.json', 'w') as f:
                json.dump(checkpoints, f)

        print(f'Region: {region} | Processed {i}...')

    out_df = out_df.append(pd.DataFrame(data=out_dict), ignore_index=False)
    out_df.to_csv(out_df_path, index=False)


if __name__ == '__main__':
    api_key = 'RGAPI-c0929ec2-6bb8-4a1e-a187-c37bc3e8894a'
    regions = ['eun1', 'euw1', 'kr', 'na1']
    divisions = ['I', 'II', 'III', 'IV']
    with open('utils/checkpoints.json', 'r') as f:
        starts = json.load(f)

    # for region in regions:
    #     for div in divisions:
    #         get_summoners(api_key, region, 'DIAMOND', div)
    # separate_summoners(regions)

    processes = []
    for region in regions:
        # processes.append(Process(target=get_accounts, args=(api_key, region, f'data/accounts_{region}.csv',
        #                                                     f'data/summoners_{region}.csv', starts[region])))
        # processes.append(Process(target=get_match_ids, args=(api_key, region, f'data/matchid_{region}.csv',
        #                                                      f'data/accounts_{region}.csv', starts[region])))
        # processes.append(Process(target=drop_duplicates, args=(region, f'data/matchid_{region}.csv')))
        processes.append(Process(target=get_matches, args=(api_key, region, f'data/matches_{region}.csv',
                                                           f'data/matchids_nodup_{region}.csv', starts[region] + 1)))

    for p in processes:
        p.start()
    for p in processes:
        p.join()
