
import os
import sys
from rdflib import Graph, URIRef, Literal, Namespace, Variable


# python脚本，接受两个参数，一个字符串，以及一个目录。
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("接受1个n3字符串作为参数！")
        sys.exit(1)

    input_string = sys.argv[1].strip()

    # input_string = '''@prefix : <#>.
    # var:x :p :o.

    # '''
    g = Graph()
    g.parse(data=input_string, format="n3")
    VAR = Namespace("http://www.w3.org/2000/10/swap/var#")
    g2 = Graph()
    for subj, pred, obj in g:
        # 替换形如 var:x 的变量为 ?x
        if isinstance(subj, URIRef) and str(subj).startswith(VAR):
            subj = f"{subj.split(VAR)[1]}"
            subj = Variable(subj)
        if isinstance(obj, URIRef) and str(obj).startswith(VAR):
            obj = f"{obj.split(VAR)[1]}"
            obj = Variable(obj)
        if isinstance(pred, URIRef) and str(pred).startswith(str(VAR)):
           pred = f"{pred.split(VAR)[1]}"
           pred = Variable(pred)
        # 将转换后的三元组添加到新图中
        g2.add((subj, pred, obj))
    print(g2.serialize(format="n3"))
    

