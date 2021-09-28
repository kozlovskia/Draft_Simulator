import json

import pandas as pd


def get_champion_scores():
    with open('data/champions.json', 'r') as f:
        champ_scores = json.load(f)

    return champ_scores


def champion_list():
    with open('data/champions.json', 'r') as f:
        champ_scores = json.load(f)

    return list(champ_scores.keys())


def available_champs(picked_champs):
    all_champs = champion_list()
    role_champs_dict = role_champions_dict()
    champions_roles_dict = champion_role_dict()

    ret = {1: all_champs.copy(), -1: all_champs.copy()}
    picked_on_state = []
    for i, champ in enumerate(picked_champs):
        ret = update_available_champs(ret, picked_on_state, champ, role_champs_dict, champions_roles_dict)
        picked_on_state.append(champ)

    return ret


def get_teams(picked_champs):
    blue_team, red_team = [], []
    for i, champ in enumerate(picked_champs):
        if i in [0, 3, 4, 7, 8]:
            blue_team.append(champ)
        else:
            red_team.append(champ)
    return blue_team, red_team


def update_available_champs(available_champs, picked_champs, champ, role_champions_dict, champions_roles_dict):
    picking_side = 1 if len(picked_champs) in [0, 3, 4, 7, 8] else -1
    if champ in available_champs[1]:
        available_champs[1].remove(champ)
    if champ in available_champs[-1]:
        available_champs[-1].remove(champ)

    champions_to_remove = role_champions_dict[champions_roles_dict[champ]]
    for c in champions_to_remove:
        if c in available_champs[picking_side]:
            available_champs[picking_side].remove(c)

    return available_champs


def champion_role_dict():
    df = pd.read_csv('data/roles.csv')
    ret = dict()
    for _, row in df.iterrows():
        ret[row.champ_name] = row.role

    return ret


def role_champions_dict():
    df = pd.read_csv('data/roles.csv')
    ret = dict()
    for role in ['top', 'jungle', 'mid', 'bot', 'support']:
        ret[role] = list(df[df['role'] == role]['champ_name'])
    return ret


def get_popularities_and_winrates():
    champ_scores = get_champion_scores()
    popularities = {k: v['popularity'] for k, v in champ_scores.items()}
    winrates = {k: v['win_probability'] for k, v in champ_scores.items()}

    return popularities, winrates


def get_available_roles(picked_champions):
    ret = {1: ['top', 'jungle', 'mid', 'bot', 'support'], -1: ['top', 'jungle', 'mid', 'bot', 'support']}
    champions_roles_dict = champion_role_dict()

    for i, champ in enumerate(picked_champions):
        picking_side = 1 if i in [0, 3, 4, 7, 8] else -1
        role = champions_roles_dict[champ]
        ret[picking_side].remove(role)

    return ret
