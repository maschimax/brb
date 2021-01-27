"""Script to create tests for knowledge bases.

Inputs:
- knowledge bases in .csv format
- knowledge bases created with xlsx2rules_csv_v3.csv can directly be read by the BRBES

Outputs:
- none

Functionalities:
- Testing:
    1) Automated execution testing
    2) Custom input testing

--------------------
Guide:
1) specify user inputs below: filename, recommendation, automated input testing or custom input testing information
2a) if Automated input testing:
    -> run
2b) if Custom input testing:
    -> create custom input
    -> specify the custom input as input for the custom_input(..) in main()
3) wait for plots
"""


import os
import random
import numpy as np
import pandas as pd
from interval import interval, inf
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm
import matplotlib.colors
import seaborn as sns
from brokenaxes import brokenaxes as ba
from typing import List, Any
from brb.brb import csv2BRB
from brb.attr_input import AttributeInput
import math

# ---------------------------------------------------------------------
# User inputs
curdir_path = '.'
filename = 'csv_BenchmarkingRuleBase_v07_low_theta_AP.csv_RefVals_AntImp-1Mglobscaled.csv'
recommendation = 'HPO technique'    # 'ML algorithm'

# Automated execution testing
runs = 1000
incompleteness = 0.5

# Custom input testing
num_algs_in_plot = 'all'    # enables showing best top X of consequents: 'all' or integer value: num_algs_in_plot=10


# ---------------------------------------------------------------------
# plot settings
mpl.rcParams['font.family'] = 'Arial'
# 179c7d is IPTgreen
palette = sns.light_palette("#179c7d", as_cmap=True)
matplotlib.cm.register_cmap("IPTgreencmap", palette)
sns.set_theme(style="whitegrid")

def enter_custom_input(A_i, X_i):
    user_inputs = A_i.copy()
    for idx, ref_val in enumerate(A_i):
        if ref_val == X_i:
            user_inputs[idx] = 1
        else:
            user_inputs[idx] = 0
    return user_inputs

def random_existing_input(model, num_runs, incomplete, rec):
    """Creates a random input using the referential
    values that are existing in the rule base.

    Args:
        model: model to create input from.
        num_runs: number of runs to evaluate.
        incomplete: takes bool or float between 0 and 1.
            if bool, '' is added to the list of referential
            values that is randomly chosen from. if float,
            this is the probability that the input for a certain
            antecedent is empty.
    """

    # create random test inputs using referential values identical with existing ones in the rule base
    res = []
    res_place = []
    counter = 0
    while counter < num_runs:
        counter += 1
        attr_input = dict()

        # generation of a list of the ref_values for each antecedent for random.choice()
        for U_i in model.U:
            ref_vals = []
            for rule in model.rules:
                if U_i in rule.A_values:
                    ref_vals.append(rule.A_values[U_i]) if rule.A_values[U_i] not in ref_vals else ref_vals
            if len(ref_vals) > 0:

                # enables random incomplete input
                if incomplete == True:
                    ref_vals.append('')
                    attr_input[U_i.name] = random.choice(ref_vals)
                elif isinstance(incomplete, float):
                    random_val = random.random()
                    if incomplete > random_val:
                        attr_input[U_i.name] = ''
                    else:
                        attr_input[U_i.name] = random.choice(ref_vals)
                else:
                    attr_input[U_i.name] = random.choice(ref_vals)

        # get recommendation for input
        X = AttributeInput(attr_input)
        belief_degrees = model.run(X)
        results = dict(zip(model.D, belief_degrees))

        # ordering starting with the highest values first
        results = {alg: results[alg] for alg in sorted(results, key=results.get, reverse=True)}
        results_place = {alg: num + 1 for num, alg in enumerate(results.keys())}
        print(results_place)
        res.append(results)
        res_place.append(results_place)

    # compute average belief degree over number of runs
    ave_result = {alg: 0 for alg in results.keys()}
    for result in res:
        ave_result = {alg: ave_result[alg] + bel for alg, bel in result.items()}
    ave_result = {alg: value / num_runs for alg, value in ave_result.items()}

    # bringing result data into boxplot plotting format
    boxplot_data = {alg: [] for alg in results.keys()}
    for result in res:
        for alg, bel in result.items():
            boxplot_data[alg].append(bel)
    # sorting
    boxplot_data = {alg: bel for alg, bel in
                    sorted(boxplot_data.items(), key=lambda i: sum(i[1]), reverse=True)}

    boxplot_data_place = {alg: [] for alg in results_place.keys()}
    for result_place in res_place:
        for alg, place in result_place.items():
            boxplot_data_place[alg].append(place)
    # sorting
    boxplot_data_place = {alg: place for alg, place in
                          sorted(boxplot_data_place.items(), key=lambda i: sum(i[1]), reverse=False)}

    # plotting results in boxplot
    if incomplete == 'True':
        complete = 'incomplete'
    else:
        complete = int(incomplete*100)

    title = '{} runs on a randomly created input of existing values. User specified {}% of the antecedents.'.format(num_runs, complete)
    boxplot_results(boxplot_data, title, y='Final belief', rec=rec)
    boxplot_results(boxplot_data_place, title, y='Average rank', rec=rec)

def custom_input(model, input, rec, show_top):
    num_runs = 1
    res = []
    res_place = []
    attr_input = dict()

    # checking how many different inputs there are
    num_inputs = len(input[next(iter(input))])
    for i in range(num_inputs):
        for U_i in model.U:
            if len(input[U_i.name]) > 1:
                attr_input[U_i.name] = input[U_i.name][i]
            else:
                attr_input[U_i.name] = input[U_i.name]
        X = AttributeInput(attr_input)
        belief_degrees = model.run(X)
        results = dict(zip(model.D, belief_degrees))

        # ordering starting with the highest values first
        results = {alg: results[alg] for alg in sorted(results, key=results.get, reverse=True)}
        print(results)
        results_place = {alg: num + 1 for num, alg in enumerate(results.keys())}
        print(results_place)
        res.append(results)
        res_place.append(results_place)

    # compute average belief degree over number of runs
    ave_result = {alg: 0 for alg in results.keys()}
    for result in res:
        ave_result = {alg: ave_result[alg] + bel for alg, bel in result.items()}
    ave_result = {alg: value / num_runs for alg, value in ave_result.items()}

    # bringing result data into boxplot plotting format
    boxplot_data = {alg: [] for alg in results.keys()}
    for result in res:
        for alg, bel in result.items():
            boxplot_data[alg].append(bel)
    # sorting
    boxplot_data = {alg: bel for alg, bel in
                    sorted(boxplot_data.items(), key=lambda i: sum(i[1]), reverse=True)}

    boxplot_data_place = {alg: [] for alg in results_place.keys()}
    for result_place in res_place:
        for alg, place in result_place.items():
            boxplot_data_place[alg].append(place)
    # sorting
    boxplot_data_place = {alg: place for alg, place in
                          sorted(boxplot_data_place.items(), key=lambda i: sum(i[1]), reverse=False)}

    # plotting results in boxplot
    title = 'Custom input'
    boxplot_custominputs_results(res, title, 'Total belief', rec=rec, show_top=show_top)
    #boxplot_results(boxplot_data, title)
    #boxplot_results(boxplot_data_place, title)

def custom_input_KO(model, model_wKO, input, rec, show_top):
    num_runs = 1
    res = []
    res_place = []
    res_wKO = []
    res_place_wKO = []
    attr_input = dict()

    # checking how many different inputs there are
    num_inputs = len(input[next(iter(input))])
    for i in range(num_inputs):
        if i < 3:
            for U_i in model_wKO.U:
                if len(input[U_i.name]) > 1:
                    attr_input[U_i.name] = input[U_i.name][i]
                else:
                    attr_input[U_i.name] = input[U_i.name]
            X = AttributeInput(attr_input)
            belief_degrees = model_wKO.run(X)
            results_wKO = dict(zip(model_wKO.D, belief_degrees))

            # ordering starting with the highest values first
            results_wKO = {alg: results_wKO[alg] for alg in sorted(results_wKO, key=results_wKO.get, reverse=True)}
            print(results_wKO)
            results_place_wKO = {alg: num + 1 for num, alg in enumerate(results_wKO.keys())}
            print(results_place_wKO)
            res_wKO.append(results_wKO)
            res_place_wKO.append(results_place_wKO)
        else:
            for U_i in model.U:
                if len(input[U_i.name]) > 1:
                    attr_input[U_i.name] = input[U_i.name][i]
                else:
                    attr_input[U_i.name] = input[U_i.name]
            X = AttributeInput(attr_input)
            belief_degrees = model.run(X)
            results = dict(zip(model.D, belief_degrees))

            # ordering starting with the highest values first
            results = {alg: results[alg] for alg in sorted(results, key=results.get, reverse=True)}
            print(results)
            results_place = {alg: num + 1 for num, alg in enumerate(results.keys())}
            print(results_place)
            res.append(results)
            res_place.append(results_place)

    # compute average belief degree over number of runs
    ave_result_wKO = {alg: 0 for alg in results_wKO.keys()}
    for result in res_wKO:
        ave_result_wKO = {alg: ave_result_wKO[alg] + bel for alg, bel in result.items()}
    ave_result_wKO = {alg: value / num_runs for alg, value in ave_result_wKO.items()}
    ave_result = {alg: 0 for alg in results.keys()}
    for result in res:
        ave_result = {alg: ave_result[alg] + bel for alg, bel in result.items()}
    ave_result = {alg: value / num_runs for alg, value in ave_result.items()}

    # bringing result data into boxplot plotting format
    boxplot_data_wKO = {alg: [] for alg in results_wKO.keys()}
    for result in res_wKO:
        for alg, bel in result.items():
            boxplot_data_wKO[alg].append(bel)
    # sorting
    boxplot_data = {alg: bel for alg, bel in
                    sorted(boxplot_data_wKO.items(), key=lambda i: sum(i[1]), reverse=True)}
    boxplot_data = {alg: [] for alg in results.keys()}
    for result in res:
        for alg, bel in result.items():
            boxplot_data[alg].append(bel)
    # sorting
    boxplot_data = {alg: bel for alg, bel in
                    sorted(boxplot_data.items(), key=lambda i: sum(i[1]), reverse=True)}

    boxplot_data_place_wKO = {alg: [] for alg in results_place_wKO.keys()}
    for result_place in res_place_wKO:
        for alg, place in result_place.items():
            boxplot_data_place_wKO[alg].append(place)
    # sorting
    boxplot_data_place_wKO = {alg: place for alg, place in
                          sorted(boxplot_data_place_wKO.items(), key=lambda i: sum(i[1]), reverse=False)}
    boxplot_data_place = {alg: [] for alg in results_place.keys()}
    for result_place in res_place:
        for alg, place in result_place.items():
            boxplot_data_place[alg].append(place)
    # sorting
    boxplot_data_place = {alg: place for alg, place in
                          sorted(boxplot_data_place.items(), key=lambda i: sum(i[1]), reverse=False)}

    # plotting results in boxplot
    title = 'Custom input'
    boxplot_custominputs_results_wKO(res, res_wKO, title, 'Total belief', rec=rec, show_top=show_top)
    #boxplot_results(boxplot_data, title)
    #boxplot_results(boxplot_data_place, title)

def boxplot_results(data: List[any], title, y, rec):
    _data = [np.asarray(results) for results in data.values()]
    _consequents = [key.split('_')[1] for key in data.keys()]

    _dict = {y: [], rec: []}
    for key in data.keys():
        for value in data[key]:
            _dict[y].append(value)
            _dict[rec].append(key.split('_')[1])
    _df = pd.DataFrame.from_dict(_dict)

    #plt.boxplot(_data, labels=_consequents)
    plt.title(title, fontsize=11)
    plt.xticks(rotation=45, ha='right', fontsize=9)

    sns.boxplot(x=rec, y=y, data=_df, color="#179c7d")

    plt.xlabel(xlabel=rec, fontsize=11)
    plt.ylabel(ylabel=y, fontsize=11)
    plt.tight_layout()

    plt.show()


def boxplot_custominputs_results(data: List[any], title, y, rec, show_top):
    sqrt = math.ceil(np.sqrt(len(data)))
    fig, axes = plt.subplots(sqrt, sqrt)

    ML_IT = False
    ML_3UCs = False
    HPO_KO = False
    HPO_IT = False
    HPO_3UCs = True

    if ML_IT:
        titles = ['Use case 1: Matching an existing rule',
                  'Use case 2: Uncertainty in input',
                  'Use case 3: Totally generic input',
                  'Use case 4: Totally specific input'
                  ]

        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]

            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #

            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)


        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif ML_3UCs:
        titles = ['Use case 1: Learning ML beginner',
                  'Use case 2: Proof-of-concept',
                  'Use case 3: High performance',
                  '-'
                 ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
            # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif HPO_KO:
        titles = [
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
            'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
            'IF {(Conditionality; yes)}'
            ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
            # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif HPO_IT:
        titles = ['Use case 1: Matching an existing rule (Rule 74)',
                  'Use case 2: Uncertainty in input',
                  'Use case 3: Totally generic input',
                  'Use case 4: Totally specific input'
                  ]
        title_HPO_KO4 = [
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
            'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
            'IF {(Conditionality; yes)}'
            ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif HPO_3UCs:
        titles = ['Use case 1: Final Performance',
                  'Use case 2: Anytime Performance',
                  'Use case 3: Robustness',
                  '-',
                  ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
            # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    title_HPO_KO1 = ['IF {(Transparency; yes)}',
                  'IF {(Transparency; must)}',
                  'IF {(Well-documented implementation; must)}',
                  'IF {(Conditionality; yes)}'
                  ]
    title_HPO_KO4 = ['IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
                     'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
                     'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
                     'IF {(Conditionality; yes)}'
                     ]
    titles_ML_IT = ['Scenario 1: Matching an existing rule',
                      'Scenario 2: Uncertainty in input',
                      'Scenario 3: Totally generic input',
                      'Scenario 4: Totally specific input'
                      ]
    titles_ML_3UCs = ['Use case 1: Learning ML beginner',
                      'Use case 2: Proof-of-concept',
                      'Use case 3: High performance',
                      '-'
                      ]

def boxplot_custominputs_results_brokenaxes(data: List[any], title, y, rec, show_top, brokenaxes):
    sqrt = math.ceil(np.sqrt(len(data)))
    fig, axes = plt.subplots(sqrt, sqrt)

    ML_IT = False
    ML_3UCs = False
    HPO_KO = True
    HPO_IT = False
    HPO_3UCs = False

    if ML_IT:
        titles = ['Use case 1: Matching an existing rule',
                  'Use case 2: Uncertainty in input',
                  'Use case 3: Totally generic input',
                  'Use case 4: Totally specific input'
                  ]

        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]

            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #

            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)


        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif ML_3UCs:
        titles = ['Use case 1: Learning ML beginner',
                  'Use case 2: Proof-of-concept',
                  'Use case 3: High performance',
                  '-'
                 ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
            # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif HPO_KO:
        titles = [
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
            'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
            'IF {(Conditionality; yes)}'
            ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]

            if brokenaxes:
                sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                            palette='IPTgreencmap')
                y_title_margin = 1.2
                # sns.set_theme(font="Arial", font_scale=6)
                axes[math.floor(idx / sqrt), idx % sqrt] = ba(ylims=((0, 0.001), (0.058, 0.06)))
                axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
                axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                         ha='right', fontsize=7)  #
                # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
                axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
                axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            else:
                sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                            palette='IPTgreencmap')
                y_title_margin = 1.2
                axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
                axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                         ha='right', fontsize=7)  #
                axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
                axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif HPO_IT:
        titles = ['Use case 1: Matching an existing rule (Rule 74)',
                  'Use case 2: Uncertainty in input',
                  'Use case 3: Totally generic input',
                  'Use case 4: Totally specific input'
                  ]
        title_HPO_KO4 = [
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
            'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
            'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
            'IF {(Conditionality; yes)}'
            ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    elif HPO_3UCs:
        titles = ['Use case 1:\nRandom Forest, TCT <10min, 1 worker',
                  'Use case 2:\nRandom Forest, TCT 8h, 8 workers',
                  'Use case 3:\nKNN, TCT >2h, transparency wished',
                  '-',
                  ]
        for idx, result in enumerate(data):
            _dict = {y: [], rec: []}
            _data = [np.asarray(result) for result in result.values()]
            _consequents = [key.split('_')[1] for key in result.keys()]

            for key in result.keys():
                _dict[y].append(result[key])
                _dict[rec].append(key.split('_')[1])
            _df = pd.DataFrame.from_dict(_dict)
            if show_top == 'all':
                pass
            else:
                _df = _df[:show_top]
                _consequents = _consequents[:show_top]
            # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
            # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
            sns.boxplot(ax=axes[math.floor(idx / sqrt), idx % sqrt], x=rec, y=y, data=_df,
                        palette='IPTgreencmap')
            y_title_margin = 1.2
            # sns.set_theme(font="Arial", font_scale=6)
            axes[math.floor(idx / sqrt), idx % sqrt].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
            axes[math.floor(idx / sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45,
                                                                     ha='right', fontsize=7)  #
            # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
            axes[math.floor(idx / sqrt), idx % sqrt].set_xlabel('')
            axes[math.floor(idx / sqrt), idx % sqrt].set_ylabel('Total belief', fontsize=9)
            # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

        fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
        plt.tight_layout()
        plt.show()

    title_HPO_KO1 = ['IF {(Transparency; yes)}',
                  'IF {(Transparency; must)}',
                  'IF {(Well-documented implementation; must)}',
                  'IF {(Conditionality; yes)}'
                  ]
    title_HPO_KO4 = ['IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
                     'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
                     'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
                     'IF {(Conditionality; yes)}'
                     ]
    titles_ML_IT = ['Scenario 1: Matching an existing rule',
                      'Scenario 2: Uncertainty in input',
                      'Scenario 3: Totally generic input',
                      'Scenario 4: Totally specific input'
                      ]
    titles_ML_3UCs = ['Use case 1: Learning ML beginner',
                      'Use case 2: Proof-of-concept',
                      'Use case 3: High performance',
                      '-'
                      ]

def boxplot_custominputs_results_wKO(data: List[any], data_wKO: List[any], title, y, rec, show_top):
    sqrt = math.ceil(np.sqrt(len(data)))

    fig, axes = plt.subplots(3, 2)

    titles_wKO = ['Rule 74 AND \n(Hardware: Number of workers...; 2)}',
              'Rule 74 AND \n(Hardware: Number of workers...; '')}',
              'IF {(Transparency; must)}\nIF {(Conditionality; yes)}'
              ]
    titles = ['Rule 74 AND \n(Hardware: Number of workers...; 2)}',
              'Rule 74 AND \n(Hardware: Number of workers...; '')}',
              'IF {(Transparency; yes)}\nIF {(Conditionality; yes)}'
              ]
    for idx, result in enumerate(data_wKO):
        _dict = {y: [], rec: []}
        _data = [np.asarray(result) for result in result.values()]
        _consequents = [key.split('_')[1] for key in result.keys()]

        for key in result.keys():
            _dict[y].append(result[key])
            _dict[rec].append(key.split('_')[1])
        _df = pd.DataFrame.from_dict(_dict)
        if show_top == 'all':
            pass
        else:
            _df = _df[:show_top]
            _consequents = _consequents[:show_top]
        # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
        # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
        sns.boxplot(ax=axes[idx, 0], x=rec, y=y, data=_df,
                    palette='IPTgreencmap')
        y_title_margin = 1.2
        # sns.set_theme(font="Arial", font_scale=6)
        axes[idx, 0].set_title(titles_wKO[idx], fontsize=9)  # , y=y_title_margin
        axes[idx, 0].set_xticklabels(labels=_consequents, rotation=45,
                                                                 ha='right', fontsize=7)  #
        # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
        axes[idx, 0].set_xlabel('')
        axes[idx, 0].set_ylabel('Total belief', fontsize=9)
        # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

    for idx, result in enumerate(data):
        _dict = {y: [], rec: []}
        _data = [np.asarray(result) for result in result.values()]
        _consequents = [key.split('_')[1] for key in result.keys()]

        for key in result.keys():
            _dict[y].append(result[key])
            _dict[rec].append(key.split('_')[1])
        _df = pd.DataFrame.from_dict(_dict)
        if show_top == 'all':

            pass
        else:
            _df = _df[:show_top]
            _consequents = _consequents[:show_top]
        # axes[math.floor(idx/sqrt), idx % sqrt].boxplot(_data)
        # axes[math.floor(idx/sqrt), idx % sqrt].set_xticklabels(labels=_consequents, rotation=45, ha='right')
        sns.boxplot(ax=axes[idx, 1], x=rec, y=y, data=_df,
                    palette='IPTgreencmap')
        y_title_margin = 1.2
        # sns.set_theme(font="Arial", font_scale=6)
        axes[idx, 1].set_title(titles[idx], fontsize=9)  # , y=y_title_margin
        axes[idx, 1].set_xticklabels(labels=_consequents, rotation=45,
                                                                 ha='right', fontsize=7)  #
        # axes[math.floor(idx / sqrt), idx % sqrt].set_yticklabels(plt.yticks(), fontsize=7)
        axes[idx, 1].set_xlabel('')
        axes[idx, 1].set_ylabel('Total belief', fontsize=9)
        # sns.set_context("paper", rc={"font.size": 7, "axes.titlesize": 9, "axes.labelsize": 7})

    fig.subplots_adjust(top=0.95, bottom=0.16, left=0.12, right=0.95, hspace=0.72, wspace=0.4)
    plt.tight_layout()
    plt.show()


    title_HPO_KO1 = ['IF {(Transparency; yes)}',
                     'IF {(Transparency; must)}',
                     'IF {(Well-documented implementation; must)}',
                     'IF {(Conditionality; yes)}'
                     ]
    title_HPO_KO4 = [
        'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}\nIF {(Conditionality; yes)}',
        'IF {(Transparency; must)}\nIF {(Well-documented implementation; must)}',
        'IF {(Transparency; must)}\nIF {(Conditionality; yes)}',
        'IF {(Conditionality; yes)}'
        ]
    titles_ML_IT = ['Scenario 1: Matching an existing rule',
                    'Scenario 2: Uncertainty in input',
                    'Scenario 3: Totally generic input',
                    'Scenario 4: Totally specific input'
                    ]
    titles_ML_3UCs = ['Use case 1: Learning ML beginner',
                      'Use case 2: Proof-of-concept',
                      'Use case 3: High performance',
                      '-'
                      ]

# inputs for klein2019 custom input
inputs_klein = {
          "Dimensionality of HPs": [8, 8, 8, 8],
          "Conditional HP Space": ['no', 'no', 'no', 'no'],
          "#continuous HPs of ML alg.": ['>=1', '0', '>=1', '0'],
          "Number of possible function evaluations/maximum number of trials": ['<100', '<100', '<100', '<100'],
          "Machine Learning Algorithm": ['SVM', 'XGBoost', 'XGBoost', 'XGBoost'],
          "Dataset to perform ML task": ['10 UCI Regression datasets', '16 OpenML classification datasets', '16 OpenML classification datasets', '16 OpenML classification datasets'],
          "Artificial noise in dataset": ['no', 'no', 'no', 'yes'],
          "Surrogate Benchmarking": ['yes', 'yes', 'yes', 'yes'],
          "Task that was performed by the ML algorithm who's HPs were optimized": ['Regression', 'Classification', 'Classification', 'Classification']}

# inputs HPO BeliefRuleBase_v9 - Bruno's three cases
inputs_HPO_BRB_v9_3cases = {
    'A_UR: quality demands':
        ['', '', 'high', 'high'],
    'A_User\'s programming ability':
        ['low', 'low', 'high', 'high'],
    'A_UR: need for model transparency':
        ['yes', '', '', 'yes'],
    'A_UR: Availability of a well documented library':
        ['yes', '', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Access to parallel computing':
        ['', '', 'yes', 'yes'],
    'A_Production use case':
        ['', '', '', ''],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Number of kernels used':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['>172800', '<7200', '>172800', '>172800'],
    'A_Machine Learning Algorithm':
        ['', '', '', ''],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['', '', '', ''],
    'A_Usage of one-hot encoding for cat. features':
        ['', '', '', ''],
    'A_Dimensionality of HPs':
        ['', '', '', ''],
    'A_Conditional HP space':
        ['', '', '', ''],
    'A_HP datatypes':
        ['', '', '', ''],
    'A_Availability of a warm-start HP configuration':
        ['', '', '', ''],
    'A_Obtainability of gradients':
        ['', '', '', ''],
    'A_Input Data':
        ['', '', '', ''],   #Image data, Tabular data
    'A_#Instances training dataset':
        ['', '', '', ''],
    'A_Ratio training to test dataset':
        ['', '', '', ''],
    'A_Dataset balance':
        ['', '', '', ''],  #imbalanced
    'A_Ratio positive to negative targets':
        ['', '', '', ''],
    'A_Noise in dataset':
        ['', '', '', ''],
    'A_Training Technique':
        ['', '', '', ''],
    'A_ML task':
        ['', '', '', ''],   #Multiclass Classification
    'A_Detailed ML task':
        ['', '', '', ''],   #Image Recognition
}

# inputs HPO BeliefRuleBase_v13 - KNOCK-OUT RULES TESTING 1
inputs_HPO_BRB_KO1_v13 = {
    'A_UR: quality demands':
        ['', '', '', ''],
    'A_User\'s programming ability':
        ['', '', '', ''],
    'A_UR: need for model transparency':
        ['yes', 'must', '', ''],
    'A_UR: Availability of a well documented library':
        ['', '', 'must', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['', '', '', ''],
    'A_Production application area':
        ['', '', '', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['', '', '', ''],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['', '', '', ''],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['', '', '', ''],
    'A_Dimensionality of HPs':
        ['', '', '', ''],
    'A_Conditional HP space':
        ['', '', '', 'yes'],
    'A_HP datatypes':
        ['', '', '', ''],
    'A_Availability of a warm-start HP configuration':
        ['', '', '', ''],
    'A_Obtainability of gradients':
        ['', '', '', ''],
    'A_Input Data':
        ['', '', '', ''],  # Image data
    'A_#Instances training dataset':
        ['', '', '', ''],
    'A_Ratio training to test dataset':
        ['', '', '', ''],
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['', '', '', ''],   # offline
    'A_ML task':
        ['', '', '', ''],   # Multiclass Classification
    'A_Detailed ML task':
        ['', '', '', ''],   # Image Recognition
}
# inputs HPO BeliefRuleBase_v13 - KNOCK-OUT RULES TESTING 2
inputs_HPO_BRB_KO2_v13 = {
    'A_UR: quality demands':
        ['high', 'high', 'high', 'high'],
    'A_User\'s programming ability':
        ['', '', '', ''],
    'A_UR: need for model transparency':
        ['yes', 'must', '', ''],
    'A_UR: Availability of a well documented library':
        ['', '', 'must', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['', '', '', ''],
    'A_Production application area':
        ['', '', '', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['7200.0:172800', '7200.0:172800', '7200.0:172800', '7200.0:172800'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['XGBoost', 'XGBoost', 'XGBoost', 'XGBoost'],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['', '', '', ''],
    'A_Dimensionality of HPs':
        ['', '', '', ''],
    'A_Conditional HP space':
        ['', '', '', 'yes'],
    'A_HP datatypes':
        ['', '', '', ''],
    'A_Availability of a warm-start HP configuration':
        ['', '', '', ''],
    'A_Obtainability of gradients':
        ['', '', '', ''],
    'A_Input Data':
        ['', '', '', ''],  # Image data
    'A_#Instances training dataset':
        ['', '', '', ''],
    'A_Ratio training to test dataset':
        ['', '', '', ''],
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', 'Offline', 'Offline'],   # Offline
    'A_ML task':
        ['Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification'],   # Multiclass Classification
    'A_Detailed ML task':
        ['', '', '', ''],   # Image Recognition
}
# inputs HPO BeliefRuleBase_v13 - KNOCK-OUT RULES TESTING 3
inputs_HPO_BRB_KO3_v13 = {
    'A_UR: quality demands':
        ['high', 'high', 'high', 'high'],
    'A_User\'s programming ability':
        ['', '', '', ''],
    'A_UR: need for model transparency':
        ['must', 'must', 'must', ''],
    'A_UR: Availability of a well documented library':
        ['must', 'must', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['', '', '', ''],
    'A_Production application area':
        ['', '', '', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['7200.0:172800', '7200.0:172800', '7200.0:172800', '7200.0:172800'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['XGBoost', 'XGBoost', 'XGBoost', 'XGBoost'],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['', '', '', ''],
    'A_Dimensionality of HPs':
        ['', '', '', ''],
    'A_Conditional HP space':
        ['yes', '', 'yes', 'yes'],
    'A_HP datatypes':
        ['', '', '', ''],
    'A_Availability of a warm-start HP configuration':
        ['', '', '', ''],
    'A_Obtainability of gradients':
        ['', '', '', ''],
    'A_Input Data':
        ['', '', '', ''],  # Image data
    'A_#Instances training dataset':
        ['', '', '', ''],
    'A_Ratio training to test dataset':
        ['', '', '', ''],
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', 'Offline', 'Offline'],   # Offline
    'A_ML task':
        ['Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification'],   # Multiclass Classification
    'A_Detailed ML task':
        ['', '', '', ''],   # Image Recognition
}
# inputs HPO BeliefRuleBase_v13 - KNOCK-OUT RULES TESTING 4 3,2
inputs_HPO_BRB_KO4_v14 = {
    'A_UR: quality demands':
        ['', '', 'high', '', '', 'high'],
    'A_User\'s programming ability':
        ['', '', '', '', '', ''],
    'A_UR: need for model transparency':
        ['', '', 'must', '', '', 'yes'],
    'A_UR: Availability of a well documented library':
        ['', '', '', '', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', '', '', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['2', '', '', '2', '', ''],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', '', 'Predictive Quality', 'Predictive Quality', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['<5', '<5', '', '<5', '<5', ''],
    'A_Running time per trial [s]':
        ['720', '720', '', '720', '720', ''],
    'A_Total Computing Time [s]':
        ['1.0:7200', '7200.0:172800', '7200.0:172800', '7200.0:172800', '7200.0:172800', '7200.0:172800'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['Multilayer Perceptron', 'Multilayer Perceptron', 'Multilayer Perceptron', 'Multilayer Perceptron', 'Multilayer Perceptron', 'Multilayer Perceptron'],
    'A_Obtainability of good approximate':
        ['', '', '', '', '', ''],
    'A_Supports parallel evaluations':
        ['', '', '', '', '', ''],
    'A_Dimensionality of HPs':
        ['>10', '>10', '', '>10', '>10', ''],
    'A_Conditional HP space':
        ['yes', 'yes', 'yes', 'yes', 'yes', 'yes'],
    'A_HP datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '', '[continuous, discrete, nominal]', '[continuous, discrete, nominal]', ''],
    'A_Availability of a warm-start HP configuration':
        ['', '', '', '', '', ''],
    'A_Obtainability of gradients':
        ['', '', '', '', '', ''],
    'A_Input Data':
        ['Image data', 'Image data', '', 'Image data', 'Image data', ''],  # Image data
    'A_#Instances training dataset':
        ['1000.0:100000', '1000.0:100000', '', '1000.0:100000', '1000.0:100000', ''],
    'A_Ratio training to test dataset':
        ['<1', '<1', '', '<1', '<1', ''],
    'A_Noise in dataset':
        ['', '', '', '', '', ''],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', 'Offline', 'Offline', 'Offline', 'Offline'],   # Offline
    'A_ML task':
        ['Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification',
         'Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification'],   # Multiclass Classification
    'A_Detailed ML task':
        ['Image Recognition', 'Image Recognition', '', 'Image Recognition', 'Image Recognition', ''],   # Image Recognition
}

# inputs HPO BeliefRuleBase_v13 - TRANSPARENCY TESTING
inputs_HPO_BRB_TRANSPARENCY_v13 = {
    'A_UR: quality demands':
        ['', 'high', 'high', 'high'],
    'A_User\'s programming ability':
        ['', '', '', ''],
    'A_UR: need for model transparency':
        ['yes', 'yes', 'must', ''],
    'A_UR: Availability of a well documented library':
        ['', '', '', 'yes'],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['', '', '', ''],
    'A_Production application area':
        ['', '', '', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['7200.0:172800', '>172800', '7200.0:172800', '7200.0:172800'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['XGBoost', 'XGBoost', 'XGBoost', 'XGBoost'],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['', '', '', ''],
    'A_Dimensionality of HPs':
        ['', '', '', ''],
    'A_Conditional HP space':
        ['', '', '', 'yes'],
    'A_HP datatypes':
        ['', '', '', ''],
    'A_Availability of a warm-start HP configuration':
        ['', '', '', ''],
    'A_Obtainability of gradients':
        ['', '', '', ''],
    'A_Input Data':
        ['', '', '', ''],  # Image data
    'A_#Instances training dataset':
        ['', '', '', ''],
    'A_Ratio training to test dataset':
        ['', '', '', ''],
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', 'Offline', 'Offline'],   # Offline
    'A_ML task':
        ['Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification', 'Multiclass Classification'],   # Multiclass Classification
    'A_Detailed ML task':
        ['', '', '', ''],   # Image Recognition
}
# inputs HPO BeliefRuleBase_v13 - input testing
""" 1) activation of an existing rule: is the outcome like the rule? -> Rule 74
    2) uncertain input: {'low': 0.5, 'medium': 0.5} does it work?
    3) very generic input that does not match any rule: does the BRBES still provide a rec?
    4) very specific input that does not match any rule: does the BRBES still provide a rec?

    """
inputs_HPO_BRB_IT_v14 = {
    'A_UR: quality demands':
        ['', '', '', 'high'],   # {'low': 1.0, 'medium': 1.0, 'high': 1.0}
    'A_User\'s programming ability':
        ['', {'medium': 0.5, 'high': 0.5}, '', 'high'],
    'A_UR: need for model transparency':
        ['', '', '', 'no'],
    'A_UR: Availability of a well documented library':
        ['', '', '', 'no'],
    'A_UR: Computer operating system':
        ['', '', '', 'Linux'],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['2.0:5', '2.0:5', '', '2.0:5'],
    'A_Production application area':
        ['', '', '', 'Predictive Quality'],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['<5', '<5', '', '<5'],
    'A_Running time per trial [s]':
        ['720', '720', '', '720'],
    'A_Total Computing Time [s]':
        ['1.0:7200', '1.0:7200', '', '1.0:7200'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['Multilayer Perceptron', 'Multilayer Perceptron', '', 'Multilayer Perceptron'],
    'A_Obtainability of good approximate':
        ['', '', '', 'yes'],
    'A_Supports parallel evaluations':
        ['', '', '', 'yes'],
    'A_Dimensionality of HPs':
        ['>10', '>10', '', '>10'],
    'A_Conditional HP space':
        ['yes', 'yes', '', 'yes'],
    'A_HP datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '', '[continuous, discrete, nominal]'], # [discrete, ordinal, nominal]
    'A_Availability of a warm-start HP configuration':
        ['', '', '', 'no'],
    'A_Obtainability of gradients':
        ['', '', '', 'no'],
    'A_Input Data':
        ['Image data', 'Image data', '', 'Image data'],  # Image data
    'A_#Instances training dataset':
        ['1000.0:100000', '1000.0:100000', '', '1000.0:100000'],
    'A_Ratio training to test dataset':
        ['<1', '<1', '', '<1'],
    'A_Noise in dataset':
        ['', '', '', 'no'],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', '', 'Offline'],   # offline
    'A_ML task':
        ['Multiclass Classification', 'Multiclass Classification', '', 'Multiclass Classification'],   # Multiclass Classification
    'A_Detailed ML task':
        ['Image Recognition', 'Image Recognition', 'Image Recognition', 'Image Recognition'],   # Image Recognition
}
inputs_HPO_BRB_IT_v16 = {
    'A_UR: quality demands':
        ['', '', '', 'high'],   # {'low': 1.0, 'medium': 1.0, 'high': 1.0}
    'A_User\'s programming ability':
        ['', {'low': 0.5, 'medium': 0.5}, '', 'high'],
    'A_UR: need for model transparency':
        ['', '', '', 'no'],
    'A_UR: Availability of a well documented library':
        ['', '', '', 'no'],
    'A_UR: Computer operating system':
        ['', '', '', 'Linux'],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['2.0:5', '2.0:5', '', '2.0:5'],
    'A_Production application area':
        ['', '', '', 'Predictive Quality'],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['<5', '<5', '', '<5'],
    'A_Running time per trial [s]':
        ['720', '720', '', '720'],
    'A_Total Computing Time [s]':
        ['1.0:7200', '1.0:7200', '', '1.0:7200'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['Multilayer Perceptron', 'Multilayer Perceptron', '', 'Multilayer Perceptron'],
    'A_Obtainability of good approximate':
        ['', '', '', 'yes'],
    'A_Supports parallel evaluations':
        ['', '', '', 'yes'],
    'A_Dimensionality of HPs':
        ['>10', '>10', '', '>10'],
    'A_Conditional HP space':
        ['yes', 'yes', '', 'yes'],
    'A_HP datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '', '[continuous, discrete, nominal]'], # [discrete, ordinal, nominal]
    'A_Availability of a warm-start HP configuration':
        ['', '', '', 'no'],
    'A_Obtainability of gradients':
        ['', '', '', 'yes'],
    'A_Input Data':
        ['Image data', 'Image data', '', 'Image data'],  # Image data
    'A_#Instances training dataset':
        ['1000.0:100000', '1000.0:100000', '', '1000.0:100000'],
    'A_Ratio training to test dataset':
        ['<1', '<1', '', '<1'],
    'A_Noise in dataset':
        ['', '', '', 'no'],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', '', 'Offline'],   # offline
    'A_ML task':
        ['Multiclass Classification', 'Multiclass Classification', '', 'Multiclass Classification'],   # Multiclass Classification
    'A_Detailed ML task':
        ['Image Recognition', 'Image Recognition', 'Image Recognition', 'Image Recognition'],   # Image Recognition
}

# inputs HPO BeliefRuleBase_v13 - VALIDATION
inputs_HPO_BRB_VAL_v14 = {
    'A_UR: quality demands':
        ['high', 'high', '', 'high'],   # {'low': 1.0, 'medium': 1.0, 'high': 1.0}
    'A_User\'s programming ability':
        ['', 'high', '', ''],
    'A_UR: need for model transparency':
        ['', '', '', ''],
    'A_UR: Availability of a well documented library':
        ['', '', '', ''],
    'A_UR: Computer operating system':
        ['Linux', 'Linux', '', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['1', '8', '', 'yes'],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', '', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['3600', '', '', '7200.0:172800'],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['Random Forest', 'Random Forest', '', ''],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['no', 'yes', '', ''],
    'A_Dimensionality of HPs':
        ['6', '6', '', ''],
    'A_Conditional HP space':
        ['no', 'no', '', 'yes'],
    'A_HP datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '', ''], # [discrete, ordinal, nominal]
    'A_Availability of a warm-start HP configuration':
        ['yes', 'no', '', ''],
    'A_Obtainability of gradients':
        ['no', 'no', '', ''],
    'A_Input Data':
        ['Tabular data', 'Tabular data', '', ''],  # Image data
    'A_#Instances training dataset':
        ['35400', '35400', '', ''],
    'A_Ratio training to test dataset':
        ['4.0', '4.0', '', ''],
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['Offline', '', '', ''],   # Offline
    'A_ML task':
        ['Binary Classification', 'Binary Classification', '', ''],   # Multiclass Classification
    'A_Detailed ML task':
        ['Part Failure', 'Part Failure', '', ''],   # Image Recognition
}
inputs_HPO_BRB_VAL_v16 = {
    'A_UR: quality demands':
        ['', 'high', 'high', ''],   # {'low': 1.0, 'medium': 1.0, 'high': 1.0}
    'A_User\'s programming ability':
        ['', 'high', 'high', ''],
    'A_UR: need for model transparency':
        ['', '', 'must', ''],
    'A_UR: Availability of a well documented library':
        ['', '', 'must', ''],
    'A_UR: Computer operating system':
        ['Linux', 'Linux', 'Linux', ''],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['1', '8', '8', ''],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', 'Predictive Quality', ''],  # 'Predictive Quality'
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['600', '28800', '>9600', ''],  # >172800, '7200.0:172800'
    'A_Machine Learning Algorithm':
        ['Random Forest', 'Random Forest', 'KNN', ''],
    'A_Obtainability of good approximate':
        ['', '', '', ''],
    'A_Supports parallel evaluations':
        ['yes', 'yes', 'yes', ''],
    'A_Dimensionality of HPs':
        ['6', '6', '5', ''],
    'A_Conditional HP space':
        ['no', 'no', 'no', ''],
    'A_HP datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '[discrete, nominal]', ''], # [discrete, ordinal, nominal]
    'A_Availability of a warm-start HP configuration':
        ['yes', 'no', 'no', ''],
    'A_Obtainability of gradients':
        ['no', 'no', 'no', ''],
    'A_Input Data':
        ['Tabular data', 'Tabular data', 'Tabular data', ''],  # Image data
    'A_#Instances training dataset':
        ['35800', '35800', '35800', ''],
    'A_Ratio training to test dataset':
        ['2.355', '2.355', '2.355', ''],
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['Offline', 'Offline', 'Offline', ''],   # Offline
    'A_ML task':
        ['Binary Classification', 'Binary Classification', 'Binary Classification', ''],   # Multiclass Classification
    'A_Detailed ML task':
        ['Part Failure', 'Part Failure', 'Part Failure', ''],   # Image Recognition
}

'''
1.	Typical user input which perfectly matches an existing rule
2.	Uncertain user input: does the BRBES provide a recommendation and is it sound?
3.	Very generic input that does not perfectly match any rule in the knowledge base: does the BRBES still provide a sound recommendation?
4.	Very specific input that does not perfectly match any rule in the knowledge base: does the BRBES still provide a sound recommendation?

'''
# inputs ML BeliefRuleBase_v5
inputs_ML_BRB_v5 = {
    'A_UR: quality demands':
        ['', '', 'high', 'high'],
    'A_User\'s programming ability':
        ['low', 'low', 'high', ''],
    'A_UR: need for model transparency':
        ['yes', '', '', ''],
    'A_UR: robustness of the model':
        ['', '', '', ''],
    'A_UR: scalability of the model':
        ['', '', '', ''],
    'A_UR: Availability of a well documented library':
        ['yes', '', '', ''],
    'A_UR: HPO or use of default values?':
        ['', '', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: access to parallel computing?':
        ['no', '', 'yes', 'yes'],
    'A_Hardware: access to high performance computing?':
        ['no', '', 'yes', 'yes'],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', 'Predictive Quality', ''],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Number of kernels used':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['>172800', '<7200', '>172800', '7200.0:172800'],
    'A_Input Data':
        ['', '', '', ''],  # Image data, Tabular data
    'A_#Instances training dataset':
        ['', '', '', ''],       # >1000000
    'A_Ratio training to test dataset':
        ['', '', '', ''],       # 2.0:9
    'A_Feature characteristics':
        ['', '', '', ''],   # [continuous, discrete, nominal, timestamp]
    'A_Number of features':
        ['', '', '', ''],      # <100
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training Technique':
        ['', '', '', ''],   # offline
    'A_ML task':
        ['', '', '', ''],   # Multiclass Classification
    'A_Detailed ML task':
        ['', '', '', ''],   # Image Recognition
}
# inputs ML BeliefRuleBase_v6
inputs_ML_BRB_v6 = {
    'A_UR: quality demands':
        ['', '', 'high', 'high'],
    'A_User\'s programming ability':
        ['low', 'low', 'high', ''],
    'A_UR: need for model transparency':
        ['yes', '', '', ''],
    'A_UR: robustness of the model':
        ['', '', '', ''],
    'A_UR: scalability of the model':
        ['', '', '', ''],
    'A_UR: Availability of a well documented library':
        ['yes', '', '', ''],
    'A_UR: HPO or use of default values?':
        ['', '', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: access to high performance computing':
        ['no', '', 'yes', 'yes'],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', 'Predictive Quality', ''],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Number of kernels used':
        ['', '', '', ''],
    'A_Total Computing Time [s]':
        ['>172800', '<7200', '>172800', '7200.0:172800'],
    'A_Input Data':
        ['', '', '', ''],  # Image data, Tabular data
    'A_#Instances training dataset':
        ['', '', '', ''],       # >1000000
    'A_Ratio training to test dataset':
        ['', '', '', ''],       # 2.0:9
    'A_Feature datatypes':
        ['', '', '', ''],   # [continuous, discrete, nominal, timestamp]
    'A_Number of features':
        ['', '', '', ''],      # <100
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training technique':
        ['', '', '', ''],   # offline
    'A_ML task':
        ['Regression', 'Binary Classification', '', ''],   # 'Multiclass Classification', 'Binary Classification'
    'A_Detailed ML task':
        ['', '', '', ''],   # Image Recognition
}

# inputs ML BeliefRuleBase_v6 INPUT TESTING
"""
1) perfect rule match w/ R_29
"""
inputs_ML_BRB_IT_v9 = {
    'A_UR: quality demands':
        ['high', 'high', '', 'high'],
    'A_User\'s programming ability':
        ['high', {'low': 0.5, 'medium': 0.5}, '', 'high'],
    'A_UR: need for model transparency':
        ['no', 'no', '', 'no'],    # 'must'
    'A_UR: robustness of the model':
        ['no', 'no', '', 'no'],
    'A_UR: scalability of the model':
        ['no', 'no', '', 'no'],
    'A_UR: Availability of a well documented library':
        ['no', 'no', '', 'no'],    # 'must'
    'A_UR: Use of default hyperparameter values?':
        ['', '', '', 'no'],
    'A_UR: Computer operating system':
        ['', '', '', 'Linux'],
    'A_Hardware: access to high performance computing':
        ['yes', 'yes', '', 'yes'],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', '', 'Predictive Quality'],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', '500'],
    'A_Running time per trial [s]':
        ['', '', '', '>200'],
    'A_Number of kernels used':
        ['', '', '', '32'],
    'A_Total Computing Time [s]':
        ['>172800', '>172800', '', '>172800'],
    'A_Input Data':
        ['Tabular data', 'Tabular data', '', 'Tabular data'],  # Image data, Tabular data
    'A_#Instances training dataset':
        ['>100000', '>100000', '', '>100000'],       # >1000000
    'A_Ratio training to test dataset':
        ['', '', '', '4.0'],       # 2.0:9
    'A_Feature datatypes':
        ['[continuous, discrete, nominal, timestamp]', '[continuous, discrete, nominal, timestamp]', '', '[continuous, discrete, nominal, timestamp]'],   # [continuous, discrete, nominal, timestamp]
    'A_Number of features':
        ['>1000', '>1000', '', '>1000'],      # <100
    'A_Noise in dataset':
        ['', '', '', 'yes'],   # yes
    'A_Training technique':
        ['Offline', 'Offline', '', 'Offline'],   # Offline
    'A_ML task':
        ['Binary Classification', 'Binary Classification', '', 'Binary Classification'],   # 'Multiclass Classification', 'Binary Classification'
    'A_Detailed ML task':
        ['Part Failure', 'Part Failure', 'Part Failure', 'Part Failure'],   # Image Recognition
}

# inputs ML BeliefRuleBase_v6 3 SCENARIOS
inputs_ML_BRB_3UCs_v9 = {
    'A_UR: quality demands':
        ['', '', 'high', ''],
    'A_User\'s programming ability':
        ['low', 'medium', 'high', ''],
    'A_UR: need for model transparency':
        ['yes', '', '', ''],    # 'must'
    'A_UR: robustness of the model':
        ['', '', '', ''],
    'A_UR: scalability of the model':
        ['', '', '', ''],
    'A_UR: Availability of a well documented library':
        ['yes', '', '', ''],    # 'must'
    'A_UR: Use of default hyperparameter values?':
        ['', 'Default values', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: access to high performance computing':
        ['no', 'yes', 'yes', ''],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', 'Predictive Quality', ''],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Number of kernels used':
        ['1', '8', '8', ''],
    'A_Total Computing Time [s]':
        ['3600', '3600', '3600', ''],
    'A_Input Data':
        ['Tabular data', 'Tabular data', 'Tabular data', ''],  # Image data, Tabular data
    'A_#Instances training dataset':
        ['35400', '35400', '35400', ''],       # >1000000
    'A_Ratio training to test dataset':
        ['4.0', '4.0', '4.0', ''],       # 2.0:9
    'A_Feature datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '[continuous, discrete, nominal]', ''],   # [continuous, discrete, nominal, timestamp]
    'A_Number of features':
        ['11', '11', '11', ''],      # <100
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training technique':
        ['Offline', 'Offline', 'Offline', ''],   # Offline
    'A_ML task':
        ['Binary Classification', 'Binary Classification', 'Binary Classification', ''],   # 'Multiclass Classification', 'Binary Classification'
    'A_Detailed ML task':
        ['Part Failure', 'Part Failure', 'Part Failure', ''],   # Image Recognition
}
inputs_ML_BRB_3UCs_v10 = {
    'A_UR: quality demands':
        ['', '', 'high', ''],
    'A_User\'s programming ability':
        ['low', 'medium', 'high', ''],
    'A_UR: need for model transparency':
        ['must', '', '', ''],    # 'must'
    'A_UR: robustness of the model':
        ['', '', '', ''],
    'A_UR: scalability of the model':
        ['', '', '', ''],
    'A_UR: Availability of a well documented library':
        ['must', '', '', ''],    # 'must'
    'A_UR: Use of default hyperparameter values?':
        ['', 'Default values', '', ''],
    'A_UR: Computer operating system':
        ['', '', '', ''],
    'A_Hardware: access to high performance computing':
        ['no', 'yes', 'yes', ''],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', 'Predictive Quality', ''],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '1', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Number of kernels used':
        ['1', '8', '8', ''],
    'A_Total Computing Time [s]':
        ['3600', '', '3600', ''],
    'A_Input Data':
        ['Tabular data', 'Tabular data', 'Tabular data', ''],  # Image data, Tabular data
    'A_#Instances training dataset':
        ['35400', '35400', '35400', ''],       # >1000000
    'A_Ratio training to test dataset':
        ['4.0', '4.0', '4.0', ''],       # 2.0:9
    'A_Feature datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '[continuous, discrete, nominal]', ''],   # [continuous, discrete, nominal, timestamp]
    'A_Number of features':
        ['11', '11', '11', ''],      # <100
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training technique':
        ['Offline', 'Offline', 'Offline', ''],   # Offline
    'A_ML task':
        ['Binary Classification', 'Binary Classification', 'Binary Classification', ''],   # 'Multiclass Classification', 'Binary Classification'
    'A_Detailed ML task':
        ['Part Failure', 'Part Failure', 'Part Failure', ''],   # Image Recognition
}
inputs_ML_BRB_3UCs_v10_2 = {
    'A_UR: quality demands':
        ['', '', 'high', ''],
    'A_User\'s programming ability':
        ['low', 'medium', 'high', ''],
    'A_UR: need for model transparency':
        ['must', '', '', ''],    # 'must'
    'A_UR: robustness of the model':
        ['', '', '', ''],
    'A_UR: scalability of the model':
        ['', '', '', ''],
    'A_UR: Availability of a well documented library':
        ['must', '', '', ''],    # 'must'
    'A_UR: Use of default hyperparameter values?':
        ['', 'yes', '', ''],
    'A_UR: Computer operating system':
        ['Linux', 'Linux', 'Linux', ''],
    'A_Hardware: access to high performance computing':
        ['no', 'yes', 'yes', ''],
    'A_Production application area':
        ['Predictive Quality', 'Predictive Quality', 'Predictive Quality', ''],  #Predictive Quality
    'A_Number of maximum function evaluations/ trials budget':
        ['', '1', '', ''],
    'A_Running time per trial [s]':
        ['', '', '', ''],
    'A_Number of kernels used':
        ['1', '8', '8', ''],
    'A_Total Computing Time [s]':
        ['3600', '', '28800', ''],
    'A_Input Data':
        ['Tabular data', 'Tabular data', 'Tabular data', ''],  # Image data, Tabular data
    'A_#Instances training dataset':
        ['35800', '35800', '35800', ''],       # >1000000
    'A_Ratio training to test dataset':
        ['2.355', '2.355', '2.355', ''],       # 2.0:9
    'A_Feature datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '[continuous, discrete, nominal]', ''],   # [continuous, discrete, nominal, timestamp]
    'A_Number of features':
        ['11', '11', '11', ''],      # <100
    'A_Noise in dataset':
        ['', '', '', ''],   # yes
    'A_Training technique':
        ['Offline', 'Offline', 'Offline', ''],   # Offline
    'A_ML task':
        ['Binary Classification', 'Binary Classification', 'Binary Classification', ''],   # 'Multiclass Classification', 'Binary Classification'
    'A_Detailed ML task':
        ['Part Failure', 'Part Failure', 'Part Failure', ''],   # Image Recognition
}

# inputs RuleType testing (kjn-mm)
inputs_rule_type_01 = {
    'A_Production application area':
        ['Predictive Maintenance', 'Predictive Maintenance', 'Predictive Maintenance'],
    'A_ML task':
        ['Regression', 'Regression', 'Regression' ],
    'A_Detailed ML task':
        ['Prediction or Remaining Useful Lifetime', 'Prediction or Remaining Useful Lifetime', 'Prediction or Remaining Useful Lifetime'],
    'A_Loss function':
        ['Customized', 'Customized', 'Customized'],
    'A_Special properties of loss function':
        ['Exponential', 'Exponential', 'Exponential'],
    'A_Training Technique':
        ['Offline', 'Offline', 'Offline' ],
    'A_Machine Learning Algorithm':
        ['XGBoost', 'XGBoost', 'XGBoost' ],
    'A_Dimensionality of HPs':
        ['9', '9', '9'],
    'A_Conditional HP space':
        ['yes', 'yes', 'yes'],
    'A_HP datatypes':
        ['[continuous, discrete, nominal]', '[continuous, discrete, nominal]', '[continuous, discrete, nominal]'],
    'A_Availability of a warm-start HP configuration':
        ['no', 'no', 'no'],
    'A_Running time per trial [s]':
        ['0.62', '0.62', '0.62'],
    'A_Total Computing Time [s]':
        ['83.88', '83.88', '83.88'],
    'A_Number of maximum function evaluations/ trials budget':
        ['200', '200', '200'],
    'A_Input Data':
        ['Tabular Data', 'Tabular Data', 'Tabular Data'],
    'A_#Instances training dataset':
        ['16584', '16584', '16584'],
    'A_Ratio training to test dataset':
        ['01:04', '01:04', '01:04'],
    'A_Hardware: Number of workers/kernels for parallel computing':
        ['1', '1', '1'],
    'A_CPU / GPU':
        ['CPU', 'CPU', 'CPU'],
    'A_UR: Computer operating system':
        ['Linux', 'Linux', 'Linux'],
    'A_UR: quality demands':
        ['high', '', ''],
    'A_UR: Anytime Performance':
        ['', 'high', ''],
    'A_UR: Robustness':
        ['', '', 'high'],
    'A_Obtainability of gradients':
        ['', '', ''],
    'A_Obtainability of good approximate':
        ['', '', ''],
    'A_Supports parallel evaluations':
        ['', '', ''],
    "A_User's programming ability":
        ['low', '', ''],
    "A_UR: need for model transparency":
        ['high', '', ''],
    'A_UR: Availability of a well documented library':
        ['', 'high', ''],
    'A_Noise in dataset':
        ['', '', 'high']
}

if __name__ == "__main__":

    # create model from rules.csv
    model = csv2BRB('csv_rulebases/' + filename,
                    antecedents_prefix='A_',
                    consequents_prefix='D_',
                    deltas_prefix='del_',
                    thetas='thetas')
    print('Model created')

    # Automated execution testing
    random_existing_input(model, num_runs=runs, incomplete=incompleteness, rec=recommendation)

    # Custom input testing
    custom_input(model, input=inputs_rule_type_01, rec='HPO technique', show_top=num_algs_in_plot)    # or 'ML algorithm', 'HPO technique', 'all'

    print('success')
