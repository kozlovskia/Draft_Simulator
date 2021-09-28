import random

import utils


def make_naive_move(state, side, by):
    popularities, winrates = utils.get_popularities_and_winrates()
    role_champions_dict = utils.role_champions_dict()
    available_roles = utils.get_available_roles(state)[side]
    available_champions = utils.available_champs(state)[side]

    if by == 'popularity':
        searched_by = [(k, float(v)) for k, v in popularities.items()]
    elif by == 'winrate':
        searched_by = [(k, float(v)) for k, v in winrates.items()]
    elif by == 'mixed':
        searched_by_dict = random.choice([popularities, winrates])
        searched_by = [(k, float(v)) for k, v in searched_by_dict.items()]
    else:
        raise NotImplementedError("only implemented by as popularity, winrate or mixed")

    selected_role = random.choice(available_roles)
    possible_picks = role_champions_dict[selected_role]

    possible_picks = list(set(possible_picks) & set(available_champions))

    searched_by = [item for item in searched_by if item[0] in possible_picks]
    searched_by = sorted(searched_by, key=lambda item: item[1], reverse=True)

    return searched_by[0][0]
