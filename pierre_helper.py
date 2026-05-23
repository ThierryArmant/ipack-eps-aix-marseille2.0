import os
from llama_index.core import SimpleDirectoryReader

def get_pierre_docs():
    if os.path.exists("gere_par_pierre.txt"):
        try:
            return SimpleDirectoryReader(input_files=["gere_par_pierre.txt"]).load_data()
        except:
            return []
    return []
