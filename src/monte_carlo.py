import random
from math import log, sqrt
from collections import defaultdict
from copy import deepcopy

import utils
from metrics import upper_hand
import time


class Node:
    def __init__(self, state, selected_side, conf_value=sqrt(2)):
        self.side = selected_side
        self.state = state
        self.conf_value = conf_value
        self.picking_side = 1 if len(state) in [0, 3, 4, 7, 8] else -1
        self.results = defaultdict(int)
        self.visits = 0
        self.parent = None
        self.children = []
        self.expanded = False
        self.available_champs = {1: [], -1: []}
        self.simulations = 0

        self.role_champions_dict = dict()
        self.champions_roles_dict = dict()

    def backpropagate(self, result):
        self.results[result] += 1
        self.visits += 1

        if self.parent:
            self.parent.backpropagate(result)

    def winner(self):
        if len(self.state) != 10:
            return 0
        blue_team, red_team = utils.get_teams(self.state)
        ally_team = blue_team if self.side == 1 else red_team
        opposing_team = red_team if self.side == 1 else blue_team
        if upper_hand(ally_team, opposing_team):
            return 1
        else:
            return -1

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def make_children(self, champions_roles_dict, role_champions_dict):
        for champ in self.available_champs[self.picking_side].copy():
            child = Node(self.state.copy(), self.side)
            available = deepcopy(self.available_champs)
            child.state.append(champ)

            child.available_champs = utils.update_available_champs(available, self.state.copy(),
                                                                   champ, role_champions_dict, champions_roles_dict)

            child.picking_side = 1 if len(child.state) in [0, 3, 4, 7, 8] else -1

            self.add_child(child)

    def get_preferred_child(self, all_simulations):
        best_children = []
        best_score = float('-inf')

        for child in self.children:
            score = child.get_score(all_simulations)

            if score > best_score:
                best_score = score
                best_children = [child]
            elif score == best_score:
                best_children.append(child)

        return random.choice(best_children)

    def get_score(self, all_simulations):
        c = self.conf_value
        exploitation_score = self.results[1] / self.visits
        exploration_score = c * sqrt(log(all_simulations) / self.simulations)

        return exploitation_score + exploration_score


class MonteCarlo:
    def __init__(self, root_node):
        self.root_node = root_node

    def calculate(self, expansion_num):
        for i in range(expansion_num):
            current_node = self.root_node
            current_node.simulations += 1
            while len(current_node.children):
                current_node = self.select(current_node, i)
                current_node.simulations += 1

            self.expand(current_node)

    def expand(self, node):
        node.make_children(self.root_node.champions_roles_dict, self.root_node.role_champions_dict)
        node.expanded = True
        for child in node.children:
            self.simulate(child)

    def simulate(self, node):
        node.simulations += 1
        available_champs = deepcopy(node.available_champs)
        picked_champions = node.state.copy()
        while not len(picked_champions) == 10:
            picking_side = 1 if len(picked_champions) in [0, 3, 4, 7, 8] else -1
            pick = random.choice(available_champs[picking_side])
            available_champs = utils.update_available_champs(available_champs, picked_champions, pick,
                                                             self.root_node.role_champions_dict,
                                                             self.root_node.champions_roles_dict)
            picked_champions.append(pick)
            # print(picked_champions)

        blue_team, red_team = utils.get_teams(picked_champions)
        ally_team = blue_team if self.root_node.side == 1 else red_team
        opposing_team = blue_team if self.root_node.side == -1 else red_team
        if upper_hand(ally_team, opposing_team):
            result = 1
        else:
            result = -1

        node.backpropagate(result)

    def select(self, node, all_simulations):
        return node.get_preferred_child(all_simulations)

    def make_choice(self):
        best_children = []
        most_visits = float('-inf')

        for child in self.root_node.children:
            if child.visits > most_visits:
                most_visits = child.visits
                best_children = [child]
            elif child.visits == most_visits:
                best_children.append(child)

        return max(best_children, key=lambda child: (child.results[1] / child.visits))


def create_root_node(initial_state, side):
    root_node = Node(initial_state.copy(), side)
    root_node.available_champs = utils.available_champs(root_node.state)

    champions_roles_dict = utils.champion_role_dict()
    role_champions_dict = utils.role_champions_dict()
    root_node.champions_roles_dict = champions_roles_dict
    root_node.role_champions_dict = role_champions_dict

    return root_node


# TODO: fix bug with root node children amount
def main():
    picked = []

    root_node = create_root_node(picked, 1)
    mcts = MonteCarlo(root_node)
    print(mcts.root_node.side)

    t0 = time.time()
    mcts.calculate(expansion_num=500)
    for child in mcts.root_node.children:
        print(f'{child.state[-1]}  --  {child.results[1]} + {child.results[-1]} = {child.visits}, {child.simulations}')
    best = mcts.make_choice()
    t1 = time.time()
    print(f'Recommended pick: {best.state[-1]} | simulation win%: {(best.results[1] / best.visits):4f}, '
          f'total visits: {best.visits}... Processed in {(t1 - t0):2f} sec(s).')


if __name__ == '__main__':
    main()
