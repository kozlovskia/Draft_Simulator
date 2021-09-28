import json

from itertools import combinations, product

import numpy as np


with open('data/champions.json') as f:
    CHAMP_SCORES = json.load(f)


def solo_impact(c):
    global CHAMP_SCORES
    return CHAMP_SCORES[c]['win_probability']


def synergy_champ2champ(c1, c2):
    global CHAMP_SCORES
    return CHAMP_SCORES[c1]['synergies'][c2]['score']


def counter_champ2champ(c1, c2):
    global CHAMP_SCORES
    return CHAMP_SCORES[c1]['counters'][c2]['score']


def synergy_champ2team(champ, allies):
    global CHAMP_SCORES
    return np.sum([synergy_champ2champ(champ, ally) for ally in allies])


def counter_champ2team(champ, oponents):
    global CHAMP_SCORES
    return np.sum([counter_champ2champ(champ, oponent) for oponent in oponents])


def equally_weighted_sum(champ, allies, oponents, type='custom'):
    if type == 'custom':
        return synergy_champ2team(champ, allies) + counter_champ2team(champ, oponents) + solo_impact(champ)
    return synergy_champ2team(champ, allies) + counter_champ2team(champ, oponents)


def composite_win_rate(allies, oponents):
    ally_pairs = list(combinations(allies, 2))
    mix_pairs = list(product(allies, oponents))
    synergy_all = np.sum([synergy_champ2champ(c1, c2) for c1, c2 in ally_pairs])
    counter_all = np.sum([counter_champ2champ(c1, c2) for c1, c2 in mix_pairs])

    return (synergy_all + counter_all) / (len(ally_pairs) + len(mix_pairs))


def upper_hand(allies, oponents):
    return int(composite_win_rate(allies, oponents) > composite_win_rate(oponents, allies))
