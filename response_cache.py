"""Cache borné de réponses mécaniquement validées, isolé par contexte/version."""
import copy
import hashlib
import json
import re
import threading
import unicodedata
from collections import OrderedDict


def answer_key(question, *, academy, public, mode, version, model, knowledge, selected_context=None):
    # Pas de suppression d'accents, chiffres ou ponctuation : éviter des collisions de sens.
    normalized=re.sub(r'\s+', ' ', unicodedata.normalize('NFKC',question)).strip().casefold()
    data=[normalized,academy,public,mode,version,model,knowledge,selected_context]
    return hashlib.sha256(json.dumps(data,ensure_ascii=False).encode()).hexdigest()


class AnswerCache:
    def __init__(self, capacity=256):
        self.capacity=capacity
        self.values=OrderedDict()
        self.lock=threading.Lock()

    def get(self,key):
        with self.lock:
            if key not in self.values:
                return None
            self.values.move_to_end(key)
            return copy.deepcopy(self.values[key])

    def put(self,key,value):
        with self.lock:
            self.values[key]=copy.deepcopy(value)
            self.values.move_to_end(key)
            while len(self.values)>self.capacity:
                self.values.popitem(last=False)


ANSWER_CACHE=AnswerCache()
