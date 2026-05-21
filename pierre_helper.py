import os
from llama_index.core import SimpleDirectoryReader

def get_pierre_docs():
    if os.path.exists("Géré par pierre.txt"):
        try:
            return SimpleDirectoryReader(input_files=["Géré par pierre.txt"]).load_data()
        except:
            return []
    return []
