import networkx as nx
import matplotlib.pyplot as plt
import itertools
from collections import defaultdict
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

    need_update = True

    person_id2name = tools.get_mapping('person', 'person', 'id', 'name',
                                       update=need_update)
    office_id2name = tools.get_mapping('office', 'office', 'id', 'name',
                                       update=need_update)
    person_name2id = tools.get_mapping('person', 'person', 'name', 'id', as_set=True,
                                       update=need_update)
    office_name2id = tools.get_mapping('office', 'office', 'name', 'id', as_set=True,
                                       update=need_update)


if __name__ == '__main__':
    preprocess()

    for p in person_name2id:
        if (len(person_name2id[p]) > 1):
            print(p, person_name2id[p], [person_id2name[str(id)]
                                         for id in person_name2id[p]])

    # for p in person_name2id:
    #    if 10 in person_name2id[p]:
    #        print(p, person_name2id[p])
