#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Desc

'''

# Hung-Hsuan Chen <hhchen1105@gmail.com>

import collections
import functools
import itertools
import numpy as np
import sys

import gensim

from scipy import spatial


class MyLog(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        for line in open(self.filename):
            yield line.split()


class Behavior2Vec(object):
    def __init__(self):
        self.behavior_embeddings = None
        self.full_model = None
        self.behavior_model = {}
        self.item_model = None
        
    def train(self, log_file, size=1, window=5):
        logs = MyLog(log_file)
        self.full_model = gensim.models.Word2Vec(logs, min_count=1, size=size, window=window)
        self.behavior_embeddings = self._gen_behavior_embedding()
        self._gen_behavior_model()
        self._gen_item_model()

    def _gen_behavior_model(self):
        for behavior in self.behavior_embeddings:
            self.behavior_model[behavior] = {'label': list(self.behavior_embeddings[behavior].keys()),
                                             'model': spatial.KDTree(list(self.behavior_embeddings[behavior].values()))}

    def _gen_item_model(self):
        item_embeddings = self._gen_item_embeddings()
        self.item_model = {'label': list(item_embeddings.keys()),
                           'model': spatial.KDTree(list(item_embeddings.values()))}

    def _gen_behavior_embedding(self):
        behavior_embeddings = collections.defaultdict(lambda: collections.defaultdict())
        for k in self.full_model.wv.vocab.keys():
            behavior, item_id = k.split('-')
            behavior_embeddings[behavior][item_id] = self.full_model.wv[k]

        # fill the missing behavior-embeddings by the average embeddings
        all_items = set(itertools.chain.from_iterable([list(behavior_embeddings[behavior].keys()) for behavior in behavior_embeddings]))
        avg_behavior_embeddings = self._gen_avg_behavior_embeddings(behavior_embeddings)
        for item_id in all_items:
            for behavior in behavior_embeddings.keys():
                if item_id not in behavior_embeddings[behavior]:
                    behavior_embeddings[behavior][item_id] = avg_behavior_embeddings[behavior]
        return behavior_embeddings

    def _gen_avg_behavior_embeddings(self, behavior_embeddings):
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

    def _gen_item_embeddings(self):
        behaviors = list(self.behavior_embeddings.keys())
        n_behaviors = len(behaviors)
        vector_size = len(list(list(self.behavior_embeddings.values())[0].values())[0])
        item_embeddings = collections.defaultdict(functools.partial(np.zeros, (vector_size * n_behaviors,)))
        for i, behavior in enumerate(self.behavior_embeddings):
            for item_id in self.behavior_embeddings[behavior]:
                item_embeddings[item_id][i * vector_size : (i+1) * vector_size] = self.behavior_embeddings[behavior][item_id]
        return item_embeddings

    def most_similar_behavior(self, cur_behavior, target_behavior_type=None, k=1, disregard_self=True):
        if target_behavior_type is None:
            # TODO..
            # 1. return the top-k for all behavior types
            # 2. combine the above lists and return the top-k labels and their corresponding distances
            #return ...
        cur_behavior_embedding = self.full_model.wv[cur_behavior]
        dists, indices = self.behavior_model[target_behavior_type]['model'].query(cur_behavior_embedding, k+1)
        if disregard_self:
            return [self.behavior_model[target_behavior_type]['label'][i] for i in indices[1:]], dists[1:]
        else:
            return [self.behavior_model[target_behavior_type]['label'][i] for i in indices[:-1]], dists[:-1]


def main(argv):
    log_file = '../data/sim-log-session-1000.txt'
    size = 300
    window = 5

    b2v_model = Behavior2Vec()
    b2v_model.train(log_file, size=size, window=window)


if __name__ == "__main__":
    main(sys.argv)
