"""Reallocate review slots using only projected model predictions."""
import numpy as np
from retain import CLASSES, keep_indices


def make_outputs(layers, kept, proposals, fraction):
    strong = layers['strong']
    deferred = []
    for c in CLASSES:
        mask = np.ones(len(strong[c]),dtype=bool)
        mask[kept[c]] = False
        deferred.extend((c, int(i), strong[c][i]) for i in np.flatnonzero(mask))
    deferred.sort(key=lambda row:-row[2].area)
    bids = proposals[:int(fraction*len(deferred))]
    extra = {c:[g for cat,g,_ in bids if cat==c] for c in CLASSES}
    restore = deferred[:len(deferred)-len(bids)]
    outputs = {name:{} for name in ('main','equal_budget','retained','added_to_original')}
    for c in CLASSES:
        original = np.asarray(strong[c],dtype=object)
        retained = original[kept[c]]
        added = np.asarray(extra[c],dtype=object)
        back = np.asarray([g for cat,_,g in restore if cat==c],dtype=object)
        outputs['retained'][c] = retained
        outputs['main'][c] = np.concatenate([retained,added])
        outputs['equal_budget'][c] = np.concatenate([outputs['main'][c],back])
        outputs['added_to_original'][c] = np.concatenate([original,added])
    assert sum(map(len,outputs['equal_budget'].values())) == sum(map(len,strong.values()))
    return outputs


def rank(layers, candidate, model):
    args = [layers[k] for k in ('strong','same','dual')]
    if candidate['method']=='strict':
        from rescue import ranked_from_layers
        return ranked_from_layers(*args, model)
    from rescue_rank import ranked_from_layers
    return ranked_from_layers(*args, model, floor=candidate['floor'])


def infer(layers, policy):
    kept=keep_indices(layers,policy['retain'])
    def apply(key):
        work = policy[key]
        rows = rank(layers,work,policy[work['method']])
        return make_outputs(layers,kept,rows,work['fraction'])
    results = apply('primary')
    results['low_fp'] = apply('low_fp')['main'] if policy['low_fp']!=policy['primary'] else results['main']
    return results
