from .chain import EncodedChain
from .text import EncodedText


def get_model_dict(thing):
    if isinstance(thing, EncodedChain):
        if thing.compiled:
            raise ValueError("Not implemented for compiled EncodedChain")
        return thing.model
    if isinstance(thing, EncodedText):
        if thing.chain.compiled:
            raise ValueError("Not implemented for compiled EncodedChain")
        return thing.chain.model
    if isinstance(thing, list):
        return dict(thing)
    if isinstance(thing, dict):
        return thing

    raise ValueError("`models` should be instances of list, dict, EncodedChain, or EncodedText")


def combine(models, weights=None):
    if weights == None:
        weights = [ 1 for _ in range(len(models)) ]

    if len(models) != len(weights):
        raise ValueError("`models` and `weights` lengths must be equal.")

    model_dicts = list(map(get_model_dict, models))
    state_sizes = [ len(list(md.keys())[0])
        for md in model_dicts ]

    if len(set(state_sizes)) != 1:
        raise ValueError("All `models` must have the same state size.")

    if len(set(map(type, models))) != 1:
        raise ValueError("All `models` must be of the same type.")

    c = {}

    for m, w in zip(model_dicts, weights):
        for state, options in m.items():
            current = c.get(state, {})
            for subseq_k, subseq_v in options.items():
                subseq_prev = current.get(subseq_k, 0)
                current[subseq_k] = subseq_prev + (subseq_v * w)
            c[state] = current

    ret_inst = models[0]

    if isinstance(ret_inst, EncodedChain):
        return EncodedChain.from_json(c)
    if isinstance(ret_inst, EncodedText):
        if any(m.retain_original for m in models):
            combined_sentences = []
            for m in models:
                if m.retain_original:
                    combined_sentences += m.parsed_sentences
            return ret_inst.from_chain(c, parsed_sentences=combined_sentences)
        else:
            return ret_inst.from_chain(c)
    if isinstance(ret_inst, list):
        return list(c.items())
    if isinstance(ret_inst, dict):
        return c
