from copy import deepcopy
import json
import os


def dict_merge(a, b):
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
            result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result


def change_to_attributedict(item):
    if isinstance(item, dict):
        new_dict = AttibuteDict()
        for key, value in item.items():
            new_dict[key] = change_to_attributedict(value)
        return new_dict
    elif isinstance(item, list):
        new_list = []
        for new_item in item:
            new_list.append(change_to_attributedict(new_item))
        return new_list
    else:
        return item

class Config(object):
    def __init__(self, path, defaults=None, prettyprint=True):
        if not defaults:
            defaults = dict()

        self.path = path
        self.defaults = defaults
        self.prettyprint = prettyprint
        self.cfg = {}

        self.load()
        self.save()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path))
        except OSError:
            pass
        with open(self.path, "w+") as handle:
            if self.prettyprint:
                json.dump(self.cfg, handle, indent=4, sort_keys=True)
            else:
                json.dump(self.cfg, handle)

    def load(self):
        try:
            os.makedirs(os.path.dirname(self.path))
        except OSError:
            pass
        try:
            open(self.path, "a+").close()  # Create file
            with open(self.path, "r+") as handle:
                cfg = json.load(handle)
        except ValueError:
            cfg = {}

        self.cfg = dict_merge(self.defaults, cfg)
        self.cfg = self.cfg

    def __getitem__(self, item):
        return self.items()[item]

    def __setitem__(self, key, value):
        self.items()[key] = value

    def items(self):
        return self.cfg


class AttibuteDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttibuteDict, self).__init__(*args, **kwargs)

    def __getattr__(self, item):
        try:
            return change_to_attributedict(super(AttibuteDict, self).__getitem__(item))
        except KeyError as e:
            raise AttributeError(item)

    def __setattr__(self, key, value):
        super(AttibuteDict, self).__setitem__(key, change_to_attributedict(value))

    def __getitem__(self, item):
        return change_to_attributedict(super(AttibuteDict, self).__getitem__(item))

    def __setitem__(self, key, value):
        super(AttibuteDict, self).__setitem__(key, change_to_attributedict(value))

    def items(self):
        return [(k, change_to_attributedict(v)) for k, v in super(AttibuteDict, self).items()]