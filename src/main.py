import time
from multiprocessing import Process

import pandas as pd

import utils
from monte_carlo import create_root_node, MonteCarlo
from naive_agent import make_naive_move
from metrics import composite_win_rate, upper_hand


def mcts_naive_simulation(initial_state, mcts_side, by, mcts_expansion_num=500):
    state = initial_state.copy()
    naive_side = 1 if mcts_side == -1 else -1
    while len(state) != 10:
        picking_side = 1 if len(state) in [0, 3, 4, 7, 8] else -1

        if picking_side == mcts_side:
            root_node = create_root_node(state, mcts_side)
            mcts = MonteCarlo(root_node)
            mcts.calculate(mcts_expansion_num)
            best = mcts.make_choice()
            state.append(best.state[-1])

        else:
            state.append(make_naive_move(state, naive_side, by))

    blue_team, red_team = utils.get_teams(state)
    allies = blue_team if mcts_side == 1 else red_team
    opponents = red_team if mcts_side == 1 else blue_team

    cwr = composite_win_rate(allies, opponents)
    up_h = upper_hand(allies, opponents)

    return cwr, up_h, state


def mcts_human_simulation(initial_state, mcts_side, mcts_expansion_num=1000):
    state = initial_state.copy()
    while len(state) != 10:
        picking_side = 1 if len(state) in [0, 3, 4, 7, 8] else -1

        if picking_side == mcts_side:
            root_node = create_root_node(state, mcts_side)
            mcts = MonteCarlo(root_node)
            mcts.calculate(mcts_expansion_num)
            best = mcts.make_choice()
            state.append(best.state[-1])

        else:
            while True:
                champ = input('Pass champion name:')
                if champ in utils.champion_list() and champ not in state:
                    break
                else:
                    print('Wrong champion... ', end='')

            state.append(champ)

        blue_team, red_team = utils.get_teams(state)
        print(f'BLUE: {blue_team}')
        print(f'RED:  {red_team}')
        print('---------------')

    blue_team, red_team = utils.get_teams(state)
    allies = blue_team if mcts_side == 1 else red_team
    opponents = red_team if mcts_side == 1 else blue_team

    cwr = composite_win_rate(allies, opponents)
    up_h = upper_hand(allies, opponents)

    return cwr, up_h


def simulate(exp_num):
    n_iter = 50
    side_dict = {1: 'blue', -1: 'red'}
    ret_df = pd.DataFrame(columns=['exp_num', 'conf_value', 'side', 'by', 'avg_upper_hand', 'num_upper_hand', 'games'])

    for conf_value in [0.0, 0.33, 0.66, 1.0, 1.33, 1.66, 2.0]:
        for side in [1, -1]:
            for by in ['winrate', 'popularity', 'mixed']:
                cum_up_h = 0.0
                for i in range(n_iter):
                    t0 = time.time()
                    print(f'exp_num: {exp_num:4} | conf_value: {conf_value:4} | side: {side:2} | by: {by:12} | '
                          f'iter: {i:4}', end='')
                    initial_state = []
                    cwr, up_h, state = mcts_naive_simulation(initial_state, side, by=by, mcts_expansion_num=exp_num)
                    cum_up_h += up_h
                    t1 = time.time()
                    print(f' | time: {round(t1 - t0, 2):4}')

                d = {'exp_num': exp_num, 'conf_value': conf_value, 'side': side_dict[side], 'by': by,
                     'avg_upper_hand': cum_up_h / n_iter, 'num_upper_hand': cum_up_h, 'games': n_iter}
                ret_df = ret_df.append(d, ignore_index=True)
                ret_df.to_csv(f'data/outputs/mcts_vs_naive_{exp_num}_mixed.csv', index=False)


def simulate_high_exp_num(conf_value):
    exp_num = 2000
    n_iter = 50
    side_dict = {1: 'blue', -1: 'red'}
    ret_df = pd.DataFrame(columns=['exp_num', 'conf_value', 'side', 'by', 'avg_upper_hand', 'num_upper_hand', 'games'])
    for side in [1, -1]:
        for by in ['popularity', 'winrate', 'mixed']:
            cum_up_h = 0.0
            for i in range(n_iter):
                t0 = time.time()
                print(f'exp_num: {exp_num:4} | conf_value: {conf_value:4} | side: {side:2} | by: {by:12} | '
                      f'iter: {i:4}', end='')
                initial_state = []
                cwr, up_h, state = mcts_naive_simulation(initial_state, side, by=by, mcts_expansion_num=exp_num)
                cum_up_h += up_h
                t1 = time.time()
                print(f' | time: {round(t1 - t0, 2):4}')

            d = {'exp_num': exp_num, 'conf_value': conf_value, 'side': side_dict[side], 'by': by,
                 'avg_upper_hand': cum_up_h / n_iter, 'num_upper_hand': cum_up_h, 'games': n_iter}
            ret_df = ret_df.append(d, ignore_index=True)
            ret_df.to_csv(f'data/outputs/mcts_vs_naive_{exp_num}_{conf_value}.csv', index=False)


def simulate_human(pro):
    n_iter = 10
    conf_value = 0.33
    side_dict = {1: 'blue', -1: 'red'}
    ret_df = pd.DataFrame(columns=['pro', 'conf_value', 'side', 'avg_upper_hand', 'num_upper_hand', 'games'])
    initial_state = []

    cum_up_h = 0.0
    for i in range(0):
        cwr, uph = mcts_human_simulation(initial_state.copy(), 1)
        cum_up_h += uph
    d = {'pro': pro, 'conf_value': conf_value, 'side': side_dict[1], 'avg_upper_hand': cum_up_h / n_iter,
         'num_upper_hand': cum_up_h, 'games': n_iter}
    ret_df = ret_df.append(d, ignore_index=True)
    ret_df.to_csv(f'data/outputs/mcts_vs_human.csv', index=False)

    cum_up_h = 0.0
    for i in range(n_iter):
        cwr, uph = mcts_human_simulation(initial_state.copy(), -1)
        cum_up_h += uph
    d = {'pro': pro, 'conf_value': conf_value, 'side': side_dict[1], 'avg_upper_hand': cum_up_h / n_iter,
         'num_upper_hand': cum_up_h, 'games': n_iter}
    ret_df = ret_df.append(d, ignore_index=True)
    ret_df.to_csv(f'data/outputs/mcts_vs_human.csv', index=False)


def main():
    exp_nums = [50, 100, 250, 400]
    processes = []
    for exp_num in exp_nums:
        processes.append(Process(target=simulate, args=(exp_num,)))

    for p in processes:
        p.start()
    for p in processes:
        p.join()


def main2():
    # conf_values = [0.0, 0.33, 0.66, 1.0, 1.33, 1.66, 2.0]
    conf_values = [1.33]
    processes = []
    for conf_value in conf_values:
        processes.append(Process(target=simulate_high_exp_num, args=(conf_value,)))

    for p in processes:
        p.start()
    for p in processes:
        p.join()


if __name__ == '__main__':
    main()
