import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import itertools
import random
import tools
import re


def get_income_data(year):
    json_data = tools.get_json()
    json_data = tools.filter_data(json_data,
                                  lambda e: e['main']['year'] == year)

    o2p = defaultdict(set)
    p2o = defaultdict(set)

    pid2name = defaultdict(str)
    oid2name = defaultdict(str)

    income = defaultdict(set)

    graph = nx.MultiGraph()

    for entry in json_data:
        person = entry['main']['person']
        office = entry['main']['office']

        pid2name[person['id']] = person['name']
        oid2name[office['id']] = office['name']

        incomes = [e['size']
                   for e in entry['incomes'] if e['relative'] == None]
        for i in incomes:
            income[person['id']].add(i)

        graph.add_node(person['id'])

        o2p[office['id']].add(person['id'])
        p2o[person['id']].add(office['id'])

    print('Total persons: ', len(pid2name))

    for o in o2p:
        po = list(o2p[o])
        for p in po[1:]:
            graph.add_edge(po[0], p)

    hist_data = []
    for cc in nx.connected_components(graph):
        off = {j for i in list(cc) for j in p2o[i]}
        # if 14 in off:
        for pid in cc:
            hist_data.append(sum(income[pid]) / 1000000.0)
    hist_data.sort()
    return hist_data


def test_income():
    hists = []
    for year in [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]:
        print(year)
        hists.append(get_income_data(year))
    plt.hist(hists, bins=100)
    plt.show()


def standardise_name(name):
    tokens = name.replace('.', ' ').split()
    assert len(tokens) >= 2 and len(tokens) <= 4, str(name)  # sanity check

    return tokens


def preprocess():
    global person_id2name, person_name2id
    global office_id2name, office_name2id
    global office2persons, person2offices

    need_update = False

    person_id2name = tools.get_mapping('person', 'person', 'id', 'name',
                                       update=need_update)
    office_id2name = tools.get_mapping('office', 'office', 'id', 'name',
                                       update=need_update)
    person_name2id = tools.get_mapping('person', 'person', 'name', 'id', as_set=True,
                                       update=need_update)
    office_name2id = tools.get_mapping('office', 'office', 'name', 'id', as_set=True,
                                       update=need_update)

    office2persons = tools.get_mapping('office', 'person', 'id', 'id', as_set=True,
                                       update=need_update)
    person2offices = tools.get_mapping('person', 'office', 'id', 'id', as_set=True,
                                       update=need_update)


def area(values):
    total = 0
    for i in range(1, len(values)):
        total += abs(values[i] - values[i-1])
    return total * 0.5


def income_analysis():
    global income_data

    json_data = tools.get_json()
    data = []
    for entry in json_data:
        year = entry['main']['year']
        person_id = entry['main']['person']['id']
        office_id = entry['main']['office']['id']
        income = sum([e['size']
                      for e in entry['incomes'] if e['relative'] != None])

        data.append([year, person_id, office_id, income])

    dframe = pd.DataFrame(data)
    dframe.columns = ['year', 'person_id', 'office_id', 'income']

    # office_name2id['Центральная избирательная комиссия'][0]
    office_id = 14
    print('office_id:', office_id)
    print('office_name:', office_id2name[str(office_id)])
    dframe = dframe.loc[dframe.loc[:, 'office_id'] == int(office_id), :]

    prs = []
    income_data = defaultdict(defaultdict)
    for p in office2persons[str(office_id)]:
        entries = dframe.loc[dframe.loc[:, 'person_id'] == int(p), :]
        values = []
        for year in range(2010, 2018+1):
            this_year = entries.loc[entries.loc[:, 'year'] == year, :]
            if this_year.shape[0] > 0:
                values.append(this_year.at[this_year.index[0], 'income'])
            else:
                values.append(None)
        income_data[p] = pd.Series(values, index=range(2010, 2018+1))
        prs.append(p)

    print('Total selected:', len(prs))

    #prs = [137, 229, 46]
    #fig, ax = plt.subplots()
    # for p in prs:
    #    ax.plot(income_data[p].index, income_data[p].values,
    #            label=person_id2name[str(p)])
    # plt.show()

    for p in prs:
        for q in prs:
            if p > q:
                relevant_years = []
                relevant_values_p = []
                relevant_values_q = []
                for year in range(2010, 2018+1):
                    if not (pd.isna(income_data[p][year]) or pd.isna(income_data[q][year])):
                        relevant_years.append(year)
                        relevant_values_p.append(income_data[p][year])
                        relevant_values_q.append(income_data[q][year])

                if len(relevant_values_p) <= 5:
                    continue

                print(relevant_values_p)

                corr = np.corrcoef(relevant_values_p,
                                   relevant_values_q)[0, 1]

                print(corr)

                if corr > 0.95:
                    print(p, person_id2name[str(p)])
                    print(q, person_id2name[str(q)])
                    print(corr)

                    fig, ax = plt.subplots()
                    ax.plot(relevant_years, relevant_values_p,
                            label=person_id2name[str(p)])
                    ax.plot(relevant_years, relevant_values_q,
                            label=person_id2name[str(q)])
                    plt.legend(loc='top left')
                    plt.show()


if __name__ == '__main__':
    preprocess()

    for o in office2persons:
        if (len(office2persons[str(o)]) > 500):
            print(o, len(office2persons[str(o)]))

    income_analysis()
    # for p in person_name2id:
    #    if (len(person_name2id[p]) > 1):
    #        print(p, person_name2id[p], [person_id2name[str(id)]
    #                                     for id in person_name2id[p]])
