#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Desc

'''

# Hung-Hsuan Chen <hhchen1105@gmail.com>
# Last Modified: Sun 21 Jan 2018 06:25:20 PM CST

import collections
import functools
import itertools
import numpy as np
import sys

import gensim


class MyLog(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        for line in open(self.filename):
            yield line.split()


def behavior2vec(log_file, size=1, window=5):
    logs = MyLog(log_file)
    model = gensim.models.Word2Vec(logs, size=size, min_count=1, window=window)
    return model


def gen_avg_behavior_embeddings(behavior_embeddings):
    avg_behavior_embeddings = {}
    for behavior in behavior_embeddings:
        for item_id in behavior_embeddings[behavior]:
            if behavior not in avg_behavior_embeddings:
                avg_behavior_embeddings[behavior] = behavior_embeddings[behavior][item_id]
            else:
                avg_behavior_embeddings[behavior] += behavior_embeddings[behavior][item_id]
    for behavior in avg_behavior_embeddings:
        avg_behavior_embeddings[behavior] /= len(behavior_embeddings[behavior])
    return avg_behavior_embeddings


def gen_behavior_embeddings(model):
    behavior_embeddings = collections.defaultdict(lambda: collections.defaultdict())
    for k in model.wv.vocab.keys():
        behavior, item_id = k.split('-')
        behavior_embeddings[behavior][item_id] = model.wv[k]

    # fill the missing behavior-embeddings by the average embeddings
    all_items = set(itertools.chain.from_iterable([list(behavior_embeddings[behavior].keys()) for behavior in behavior_embeddings]))
    avg_behavior_embeddings = gen_avg_behavior_embeddings(behavior_embeddings)
    for item_id in all_items:
        for behavior in behavior_embeddings.keys():
            if item_id not in behavior_embeddings[behavior]:
                behavior_embeddings[behavior][item_id] = avg_behavior_embeddings[behavior]

    return behavior_embeddings


def gen_item_embeddings(behavior_embeddings):
    behaviors = list(behavior_embeddings.keys())
    n_behaviors = len(behaviors)
    vector_size = len(list(list(behavior_embeddings.values())[0].values())[0])
    item_embeddings = collections.defaultdict(functools.partial(np.zeros, (vector_size * n_behaviors,)))
    for i, behavior in enumerate(behavior_embeddings):
        for item_id in behavior_embeddings[behavior]:
            item_embeddings[item_id][i * vector_size : (i+1) * vector_size] = behavior_embeddings[behavior][item_id]
    return item_embeddings


def main(argv):
    log_file = '../data/sim-log-session-1000.txt'
    size = 300
    window = 5

    model = behavior2vec(log_file, size=size, window=window)
    behavior_embeddings = gen_behavior_embeddings(model)
    item_embeddings = gen_item_embeddings(behavior_embeddings)


if __name__ == "__main__":
    main(sys.argv)