import tempfile
import subprocess


def read_from_file(file_path):
    '''从文件读取字符串'''
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


#测试变量的rdflib的处理
from rdflib import Graph, URIRef, Literal, Namespace
n3_string = '''@prefix : <#>.
?x :p :o.

'''
g = Graph()
g.parse(data=n3_string, format="n3")
print(g.serialize(format="n3"))

for subj, pred, obj in g:
        print(f"Subject: {subj}, Predicate: {pred}, Object: {obj}")