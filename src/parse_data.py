import requests
import json
from itertools import combinations
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D

import utils
from metrics import upper_hand


def postprocess_api_data():
    regions = ['eun1', 'euw1', 'kr', 'na1']
    dataframes = [pd.read_csv(f'data/matches_{region}.csv') for region in regions]
    df = pd.concat(dataframes, axis=0)
    df.drop_duplicates(subset=['gameId'], keep='last', inplace=True)
    print(df['gameId'].duplicated().any())

    df.to_csv('data/matches_data.csv', index=False)


def get_champion_keys():
    out_dict = dict()
    URL = 'http://ddragon.leagueoflegends.com/cdn/11.7.1/data/en_US/champion.json'
    response = requests.get(URL)
    response_json = response.json()

    for champ in response_json['data'].values():
        out_dict[champ['key']] = champ['name']

    return out_dict


def champ_win_probability_and_popularity(champ_key):
    df = pd.read_csv('data/matches_data.csv')
    champ_columns = [f'participant_{i}_champ' for i in range(1, 11)]
    champ_df = df[df[champ_columns].isin([int(champ_key)]).any(axis=1)]

    total_games = float(len(df.index))
    popularity = float(len(champ_df.index)) / total_games

    total_games_with_champ = float(len(champ_df.index))
    wins = 0.0
    for _, game in champ_df.iterrows():
        p_id = -1
        for i in range(1, 11):
            if game[f'participant_{i}_champ'] == int(champ_key):
                p_id = i
                break
        winner = game['winner']
        win = 1 if game[f'participant_{p_id}_team'] == winner else 0

        wins += win

    win_probability = wins / total_games_with_champ
    print(f'Win probability: {win_probability}    |    Popularity: {popularity}')

    return win_probability, popularity


def synergy_and_counter(champ1_key, champ2_key):
    """ counter -> champ1 counters champ2 """
    df = pd.read_csv('data/matches_data.csv')
    champ_columns = [f'participant_{i}_champ' for i in range(1, 11)]
    champs_df = df[df[champ_columns].isin([int(champ1_key)]).any(axis=1)]
    champs_df = champs_df[champs_df[champ_columns].isin([int(champ2_key)]).any(axis=1)]

    total_games = float(len(df.index))
    total_synergy_games, total_counter_games = 0.0, 0.0
    synergy_wins, counter_wins = 0.0, 0.0
    for _, game in champs_df.iterrows():
        p1_id, p2_id = -1, -1
        stop = 0
        for i in range(1, 11):
            if game[f'participant_{i}_champ'] == int(champ1_key):
                p1_id = i
                stop += 1
            if game[f'participant_{i}_champ'] == int(champ2_key):
                p2_id = i
                stop += 1
            if stop == 2:
                break
        p1_team = game[f'participant_{p1_id}_team']
        p2_team = game[f'participant_{p2_id}_team']
        winner = game['winner']

        if p1_team == p2_team:
            total_synergy_games += 1
            if p1_team == winner:
                synergy_wins += 1
        else:
            total_counter_games += 1
            if p1_team == winner:
                counter_wins += 1

    synergy_win_probability = synergy_wins / total_synergy_games
    counter_win_probability = counter_wins / total_counter_games
    synergy_popularity = total_synergy_games / total_games
    counter_popularity = total_counter_games / total_games
    print(f'Synergy win probability: {synergy_win_probability}    |    Synergy popularity: {synergy_popularity}')
    print(f'Counter win probability: {counter_win_probability}    |    Counter popularity: {counter_popularity}')

    return synergy_win_probability, synergy_popularity, counter_win_probability, counter_popularity


def champions_to_json():
    champs = get_champion_keys()
    out_dict = dict()
    for champ_key, champ_name in champs.items():
        print(f'----------------- Processing {champ_name}...')
        rest_champs = champs.copy()
        del rest_champs[champ_key]
        win_prob, popularity = champ_win_probability_and_popularity(champ_key)
        synergies, counters = dict(), dict()
        for champ2_key, champ2_name in rest_champs.items():
            print(f'Counting synergies and counters: {champ_name} -> {champ2_name}...')
            synergy, synergy_popularity, counter, counter_popularity = synergy_and_counter(champ_key, champ2_key)
            synergies[champs[champ2_key]] = dict(score=synergy, popularity=synergy_popularity)
            counters[champs[champ2_key]] = dict(score=counter, popularity=counter_popularity)
        champ_dict = {'key': champ_key, 'popularity': popularity, 'win_probability': win_prob,
                      'synergies': synergies, 'counters': counters}
        out_dict[champs[champ_key]] = champ_dict

    with open('data/champions.json', 'w') as json_file:
        json.dump(out_dict, json_file)


def cwr_accuracy():
    df = pd.read_csv('data/matches_data.csv')
    champ_scores = utils.get_champion_scores()
    champs_map_dict = {int(v['key']): k for k, v in champ_scores.items()}
    correct = 0
    for iter, r in df.iterrows():
        print(f'{iter:8d} / {len(df)}')
        blue_team, red_team = [], []
        for i in range(1, 11):
            champ_key = int(r[f'participant_{i}_champ'])
            champ_name = champs_map_dict[champ_key]
            team = int(r[f'participant_{i}_team'])
            if team == 100:
                blue_team.append(champ_name)
            elif team == 200:
                red_team.append(champ_name)
            else:
                raise ValueError(f'Incorrect team key:  {team}')

        winner = int(r['winner'])

        predicted_winner = 100 if upper_hand(blue_team, red_team) else 200

        if winner == predicted_winner:
            correct += 1

    ret = correct / len(df)
    with open('data/upper_hand_accuracy.txt', 'w') as f:
        f.write(str(ret))

    return ret


def generate_plots():
    parent_dir = Path('data/outputs')
    dfs = []
    for path in parent_dir.iterdir():
        if str(path).endswith('.csv'):
            dfs.append(pd.read_csv(path))

    df = pd.concat(dfs, ignore_index=True)
    bys = ['popularity', 'winrate', 'mixed']
    conf_values = [0.0, 0.33, 0.66, 1.0, 1.33, 1.66, 2.0]
    exp_nums = [50, 100, 400, 1000, 2000]
    for by in bys:
        sub_df = df[df.by == by]
        fig = plt.figure(figsize=(15, 10))
        gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
        (ax1, ax2, ax3), (ax4, ax5, ax6) = gs.subplots()
        fig.suptitle('Średnia wartość upper hand w zależności od parametru eksploracji')
        plots = [ax1, ax2, ax3, ax4, ax5]
        for exp_num, ax in zip(exp_nums, plots):
            ax.set_title(f'N = {exp_num}')
            subsub_df = sub_df[sub_df.exp_num == exp_num]
            subsub_df.sort_values(by='conf_value', inplace=True)
            blue_df = subsub_df[subsub_df.side == 'blue']
            red_df = subsub_df[subsub_df.side == 'red']

            x_values = subsub_df.conf_value.unique()
            blue_avg_upper_hands = list(blue_df.avg_upper_hand)
            red_avg_upper_hands = list(red_df.avg_upper_hand)

            line_blue, = ax.plot(x_values, blue_avg_upper_hands, '-o', color='blue', alpha=0.75, label='drużyna niebieska')
            line_red, = ax.plot(x_values, red_avg_upper_hands, '-o', color='red', alpha=0.75, label='drużyna czerwona')
            # plt.legend(handles=[line_blue, line_red])
            ax.legend(handles=[line_blue, line_red], handler_map={line_blue: HandlerLine2D(numpoints=1), line_red: HandlerLine2D(numpoints=1)})
            ax.plot([-0.1, 2.1], [0.5, 0.5], '--', color='gray')
            ax.set_xlim([-0.1, 2.1])
            ax.set_xticks(x_values)
            ax.set_ylim([0, 1.1])
            ax.set_yticks(np.arange(0, 1.2, 0.1))
            ax.set(xlabel='parametr eksploracji - c', ylabel='średni upper hand')
        ax6.set_visible(False)
        plt.savefig(f'data/outputs/graph_{by}.png')


if __name__ == '__main__':
    # df = pd.read_csv('data/matches_data.csv')
    # print(df['gameId'].duplicated().any())
    # postprocess_api_data()
    # champions_to_json()
    # r = cwr_accuracy()
    generate_plots()
