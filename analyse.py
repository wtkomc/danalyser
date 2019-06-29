import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
import seaborn as sns
import itertools
import random
import tools
import re
import warnings


def noop(*args, **kwargs): pass


warnings.warn = noop

# TODO


def standardise_name(name):
    tokens = name.replace('.', ' ').split()
    assert len(tokens) >= 2 and len(tokens) <= 4, str(name)  # sanity check

    return tokens


def preprocess():
    global person_id2name, person_name2id
    global office_id2name, office_name2id
    global office2persons, person2offices
    global carbrand

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

    carbrand = tools.get_cars(update=need_update)


def income_self_vs_rel(office_id=14):
    global income_data

    json_data = tools.get_json()
    data = []
    for entry in json_data:
        year = entry['main']['year']
        person_id = entry['main']['person']['id']
        office_id = entry['main']['office']['id']
        income_self = sum([e['size']
                           for e in entry['incomes'] if e['relative'] == None])
        income_rel = sum([e['size']
                          for e in entry['incomes'] if e['relative'] != None])

        data.append([year, person_id, office_id, income_self,
                     income_rel, income_self + income_rel])

    dframe = pd.DataFrame(data)
    dframe.columns = ['year', 'person_id', 'office_id',
                      'income_self', 'income_rel', 'income_total']

    print('office_id:', office_id)
    print('office_name:', office_id2name[str(office_id)])
    dframe = dframe.loc[dframe.loc[:, 'office_id'] == int(office_id), :]

    persons = set()
    income_data_self = defaultdict()
    income_data_rel = defaultdict()
    income_data_total = defaultdict()
    for p in office2persons[str(office_id)]:
        entries = dframe.loc[dframe.loc[:, 'person_id'] == int(p), :]
        values_self = []
        values_rel = []
        values_total = []
        for year in range(2006, 2018+1):
            this_year = entries.loc[entries.loc[:, 'year'] == year, :]
            if this_year.shape[0] > 0:
                values_self.append(
                    this_year.at[this_year.index[0], 'income_self'])
                values_rel.append(
                    this_year.at[this_year.index[0], 'income_rel'])
                values_total.append(
                    this_year.at[this_year.index[0], 'income_total'])
            else:
                values_self.append(None)
                values_rel.append(None)
                values_total.append(None)
        income_data_self[p] = pd.Series(values_self, index=range(2006, 2018+1))
        income_data_rel[p] = pd.Series(values_rel, index=range(2006, 2018+1))
        income_data_total[p] = pd.Series(
            values_total, index=range(2006, 2018+1))
        prs.add(p)

    print('Total selected:', len(prs))

    for p in persons:
        relevant_years = []
        relevant_values_self = []
        relevant_values_rel = []

        for year in range(2006, 2018+1):
            if not (pd.isna(income_data_self[p][year]) or pd.isna(income_data_rel[p][year])):
                relevant_years.append(year)
                relevant_values_self.append(
                    income_data_self[p][year] / 1000000.0)
                relevant_values_rel.append(
                    income_data_rel[p][year] / 1000000.0)

        if len(relevant_years) <= 5 or sum(relevant_values_rel) == 0.0:
            continue

        corr = np.corrcoef(relevant_values_self, relevant_values_rel)[0, 1]

        if corr < -0.7:
            print(p, corr, relevant_values_self, relevant_values_rel)
            fig, ax = plt.subplots()
            ax.plot(relevant_years, relevant_values_self,
                    label=person_id2name[str(p)])
            ax.plot(relevant_years, relevant_values_rel, label='relatives')
            plt.legend(loc='upper left')
            plt.show()


def abbreviate_name(name):
    words = name.split()
    return ''.join([w[0] for w in words])


def income_clustering(year):
    json_data = tools.get_json()
    json_data = tools.filter_data(
        json_data, lambda e: e['main']['year'] == year)
    json_data = tools.filter_data(
        json_data, lambda e: e['main']['office']['id'] == 14)

    data = []
    persons = []

    for entry in json_data:
        person_id = entry['main']['person']['id']
        income_self = sum([e['size']
                           for e in entry['incomes'] if e['relative'] == None])
        income_rel = sum([e['size']
                          for e in entry['incomes'] if e['relative'] != None])

        data.append([income_self, income_rel])
        persons.append(person_id)

    dframe = pd.DataFrame(data, index=persons)
    dframe.columns = ['income_self', 'income_rel']

    print(dframe)

    classifier = hdbscan.HDBSCAN(min_cluster_size=5).fit(dframe)
    classified = []
    for label in set(filter(lambda x: x >= 0, classifier.labels_)):
        print('Cluster label: ', label)
        ids = [i for i, x in enumerate(classifier.labels_) if x == label]
        for i in ids:
            print(persons[i], person_id2name[str(persons[i])], data[i])
            classified.append((label, persons[i], data[i][0], data[i][1]))
        print('\n')

    colour_palette = sns.color_palette('deep', 20)
    cluster_colours = [colour_palette[x[0]] for x in classified]
    cluster_member_colours = [sns.desaturate(x, p)
                              for x, p in zip(cluster_colours, classifier.probabilities_)]
    dx = [x[2] for x in classified]
    dy = [x[3] for x in classified]
    plt.scatter(x=dx, y=dy,
                s=10, linewidth=0, c=cluster_member_colours, alpha=1)
    plt.show()


def income_overall_analysis(year=2018):
    json_data = tools.get_json()
    json_data = tools.filter_data(json_data,
                                  lambda e: e['main']['year'] == year)

    # offices of interest
    # offices = [5, 4, 191, 4199, 482, 5963, 1397, 5953, 598, 979, 14, 607, 450]
    offices = [1, 3, 4, 5, 7, 14, 15, 17, 113,
               146, 449, 450, 453, 456, 461, 467, 594, 595, 596]
    json_data = tools.filter_data(json_data,
                                  lambda e: int(e['main']['office']['id']) in offices)

    income = np.array([], dtype=[('person_id', 'i8'), ('office_id', 'i8'),
                                 ('income_self', 'float64'), ('income_rel', 'float64'),
                                 ('income_total', 'float64')])

    for entry in json_data:
        person_id = int(entry['main']['person']['id'])
        office_id = int(entry['main']['office']['id'])
        income_self = sum([e['size'] for e in entry['incomes']
                           if e['relative'] == None])
        income_rel = sum([e['size'] for e in entry['incomes']
                          if e['relative'] != None])
        income = np.append(income, np.array([(person_id, office_id, income_self, income_rel,
                                              income_self + income_rel)], dtype=income.dtype))

    # List offices and abbreviations
    for o in offices:
        print(o, office_id2name[str(o)],
              abbreviate_name(office_id2name[str(o)]))

    # Plot 1: income in each office of interest
    N = len(offices)
    dx = []
    dy = []
    for x in range(N):
        income_slice = np.array([item for item in income
                                 if int(item['office_id']) == offices[x]], dtype=income.dtype)
        for y in income_slice:
            if y['income_rel'] / 1000000.0 < 10:
                dx.append(x)
                dy.append(y['income_self'] / 1000000.0)

    plot1 = plt.scatter(x=dx, y=dy, s=5)
    plt.ylabel('income (rel), millions of RUB')
    plt.xticks(range(N),
               [abbreviate_name(office_id2name[str(o)]) for o in offices])
    plt.show()


def mistrust_index(year=2018):
    json_data = tools.get_json()
    json_data = tools.filter_data(json_data,
                                  lambda e: e['main']['year'] == year)

    rating = defaultdict(int)
    scored = defaultdict(int)

    for entry in json_data:
        person_id = entry['main']['person']['id']
        score = 0

        # 1: total income is low, but savings are huge
        income = sum([e['size'] for e in entry['incomes']])
        savings = 0
        for s in entry['savings']:
            size = float(s.split('руб.')[0].replace(' ', '').replace(',', '.'))
            savings += size
        if (income > 0 and savings / income >= 5.0) or (income == 0 and savings > 0):
            score += 1
            scored[1] += 1

        # 2: personal income is low, but the relatives' income is huge
        income_self = sum([e['size'] for e in entry['incomes']
                           if e['relative'] == None])
        income_rel = sum([e['size'] for e in entry['incomes']
                          if e['relative'] != None])
        if (income_self > 0 and income_rel / income_self >= 5.0) or (income_self == 0 and income_rel > 0):
            score += 1
            scored[2] += 1

        # 3: zero total income(can be due to incorrectly submitted declaration, but still not good)
        if income == 0:
            score += 1
            scored[3] += 1

        # 4: low income, but owns a lot in real estate
        estates_area = 0
        for estate in entry['real_estates']:  # shall we exclude relatives?
            if not estate['square']:
                continue
            total = float(estate['square'])
            if estate['share']:
                total *= float(estate['share'])
            estates_area += total
        if income / 1000000.0 < 1.0 and estates_area > 500.0:
            score += 1
            scored[4] += 1

        # 5: lux cars
        lux_cars = [
            {'parent_name': 'BMW', 'name': '3 series'},
            {'parent_name': 'BMW', 'name': '5 series'},
            {'parent_name': 'BWM', 'name': '7 series'},
            {'parent_name': 'Acura', 'name': 'Acura'},
            {'parent_name': 'Audi', 'name': 'A4'},
            {'parent_name': 'Audi', 'name': 'A6'},
            {'parent_name': 'Audi', 'name': 'A7'},
            {'parent_name': 'Audi', 'name': 'A8'},
            {'parent_name': 'Alfa Romeo', 'name': 'Giulietta'},
            {'parent_name': 'Bentley'},
            {'parent_name': 'Cadillac'},
            {'parent_name': 'Ferrari'},
            {'parent_name': 'Hummer'},
            {'parent_name': 'Infinity'},
            {'parent_name': 'Jaguar'},
            {'parent_name': 'Lamborghini'},
            {'parent_name': 'Land Rover'},
            {'parent_name': 'Lexus'},
            {'parent_name': 'Maserati'},
            {'parent_name': 'Mercedes-Benz', 'name': 'C-класс'},
            {'parent_name': 'Mercedes-Benz', 'name': 'E-класс'},
            {'parent_name': 'Mercedes-Benz', 'name': 'GL-класс'},
            {'parent_name': 'Mercedes-Benz', 'name': 'S-класс'},
            {'parent_name': 'Porsche'},
            {'parent_name': 'Rolls-Royce'},
            {'parent_name': 'Saab', 'name': '9-3'},
            {'parent_name': 'Saab', 'name': '9-5'},
            {'parent_name': 'Volkswagen', 'name': 'Phaeton'},
            {'parent_name': 'Volvo', 'name': 'S60'},
            {'parent_name': 'Volvo', 'name': 'S80'}
        ]

        has_lux = 0
        for vehicle in entry['vehicles']:
            if not vehicle['brand']:
                continue

            for item in lux_cars:
                if 'name' in item:
                    for brand in carbrand:
                        if brand['parent_name'] == item['parent_name'] and brand['name'] == item['name'] and brand['id'] == vehicle['brand']['id']:
                            has_lux = 1
                else:
                    for brand in carbrand:
                        if brand['parent_name'] == item['parent_name'] and brand['id'] == vehicle['brand']['id']:
                            has_lux = 1

        score += has_lux
        scored[5] += has_lux

        rating[person_id] += score

    return rating


if __name__ == '__main__':
    preprocess()

    rating = mistrust_index(2014)
    # print those with rating > 2
    for p in rating:
        if rating[p] > 2:
            print(p, person_id2name[str(p)])
