import subprocess
from rdflib import Graph, URIRef, Literal, Namespace
from typing import Optional
import tempfile

# 1. rdflib在处理n3的时候有诸多bug：1.打乱规则中的语句的顺序。2. 将后向链接规则错误地解析为前向链接规则 3.将subject的列表序列化成rdf:first/rest的形式
# 因为上述原因，python调用eye有缺点。返回的n3必须要用rdflib解析，可能出bug. 
# 2. 另一种可行思路是用python实现eye可调用的自定义builtin函数，然后用eye来调用python。但是流程将不受控制。
# 3. 关于图拼接： 如上所述rdflib有各种bug。 eye推理器的--pass-merge 和 log:semantics也有bug。最保险的做法是自己拼接n3字符串。

# 4. TODO 设置arg_n3、调用eye_query、然后对返回结果进行collect_answers的这个过程，可以封装成一个函数。 比如自动清空arg_n3，以及根据合并collect_answer和get_answer
# 5. TODO 封装一个N3类，将write_to_file之类的都作为它的方法
# 6. TODO 处理update-world.n3中的绝对路径的问题。 可以将tempfile创建文件的路径改成这个项目根目录下的tmp目录
# 7. TODO 多个属性的加点动作应该是一个整体。
# 8. TODO 只要有可行动作就不断循环，除非用户执行了跳过，或者只剩下跳过的动作。
# 9. TODO 后果分支ifthenelse。（ 如果是多个独立的结果，应该依次计算概率或者全都发生。）
# 10. TODO 应该直接计算动作结果对应的那个diff-patch，存储到action-outcomes里。
# 11. TODO 多个事件可以互斥。 如果同时发生了，会用类似拒绝采样的方法重新采样。所以如果一组互斥事件的概率和太大，算法效率很低。有空改进
# 12. TODO 允许手动输入自然语言的动作描述。允许手动输入自然语言的事件描述

def write_to_file(n3_string, file_path):
    '''将字符串写入文件'''
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(n3_string)

def read_from_file(file_path):
    '''从文件读取字符串'''
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def get_answers(n3_string: str, subject= None, predicate = None) -> Optional[URIRef]:
    '''n3字符串中提取形如 {:answer :is （x1 x2 x3）.}的结果(如果有多个这样的三元组，只处理第一个), 返回rdflib的URIRef对象列表。
        如果是 {:answer :is x1}，则返回x1.
    '''
    if subject is None:
        subject = URIRef("http://semex.sigmanoise.com/r3/life-sim#answer")
    if predicate is None:
        predicate = URIRef("http://semex.sigmanoise.com/r3/life-sim#is")
    answers = [] # 用于存储动作的列表
    g = Graph()
    g.parse(data=n3_string, format="n3")
    
    for a in g.objects(subject=subject, predicate=predicate):
        for item in g.items(a):
            answers.append(item)
        if answers:
            return answers
        else:
            return a
            
    
    return None 


def collect_answers(n3_string: str, subject= None, predicate = None) -> list:
    '''n3字符串中提取形如{:answer :has x1, x2, x3.}结果, 返回rdflib的URIRef对象列表'''
    if subject is None:
        subject = URIRef("http://semex.sigmanoise.com/r3/life-sim#answer")
    if predicate is None:
        predicate = URIRef("http://semex.sigmanoise.com/r3/life-sim#has")
    answers = [] # 用于存储动作的列表
    g = Graph()
    g.parse(data=n3_string, format="n3")
    
    for answer in g.objects(subject=subject, predicate=predicate):
        answers.append(answer)
    
    return answers

# eye --pass-merged也有bug，对于引用图中的全称变量，会把它变成存在变量。例如 :s :p {?x :q :y}.
# def eye_merge(*input_files):    
#     '''运行EYE推理器，合并多个n3文件，返回合并结果. n3格式的字符串'''
#     command = ["eye"] + list(input_files) + ["--quiet" , "--nope" , "--pass-merged"]
#     result = subprocess.run(command, capture_output=True, text=True)
    

#     if result.returncode == 0:
#         return result.stdout
#     else:
#         print("Error:", result.stderr)
#         return None


def merge_n3(*n3_strings):
    '''简单拼合多个n3字符串，返回合并结果. n3格式的字符串'''
    merged_n3 = ""
    for n3 in n3_strings:
        merged_n3 += n3 + "\n"
    return merged_n3

def merge_n3_files(*input_files):
    '''简单拼合多个n3文件，返回合并结果. n3格式的字符串'''
    merged_n3 = ""
    for file in input_files:
        with open(file, 'r', encoding='utf-8') as f:
            merged_n3 += f.read() + "\n"
    return merged_n3


def eye_inference(*n3_strings):
    '''运行EYE推理器，返回推理结果. 输入是n3字符串，输出也是n3字符串'''


    # 将n3strings写入临时文件
    with tempfile.NamedTemporaryFile(delete=True, mode='w', encoding='utf-8') as temp_file:
        for n3 in n3_strings:
            temp_file.write(n3 + "\n")
        temp_file.flush()
        temp_file.seek(0)
        input_file = temp_file.name


        command = ["eye", input_file, "--quiet", "--nope", "--pass-only-new"]
        
        # 执行命令
        # cwd="/Users/Shared/code/人生重开模拟器"
        result = subprocess.run(command, cwd="./", capture_output=True, text=True)
        
        # 检查是否成功
        if result.returncode == 0:
            #print("DEBUG: EYE Reasoner executed successfully!")
            #print(read_from_file(input_file))
            #print(result.stdout)
            return result.stdout
        else:
            print("Error:", result.stderr)
            return None

# def eye_query(query_file, *input_file):
#     '''运行EYE推理器，返回查询结果. n3格式的字符串'''
#     command = ["eye"] + list(input_file) + ["--quiet" , "--nope" , "--query", query_file]
    
#     # 执行命令
#     result = subprocess.run(command, capture_output=True, text=True)
    
#     # 检查是否成功
#     if result.returncode == 0:
#         print("DEBUG: EYE Reasoner executed successfully!")
#         print(result.stdout)
#         return result.stdout
#     else:
#         print("Error:", result.stderr)
#         return None

def eye_query(query_n3, *n3_strings):
    '''运行EYE推理器，返回查询结果. n3格式的字符串'''
    # 将n3strings写入临时文件
    with tempfile.NamedTemporaryFile(delete=True, mode='w', encoding='utf-8') as temp_file:
        for n3 in n3_strings:
            temp_file.write(n3 + "\n")
        temp_file.flush()
        temp_file.seek(0)
        input_file = temp_file.name

        # 将query_n3写入另一个临时文件
        with tempfile.NamedTemporaryFile(delete=True, mode='w', encoding='utf-8') as query_temp_file:
            query_temp_file.write(query_n3)
            query_temp_file.flush()
            query_temp_file.seek(0)
            query_file = query_temp_file.name

            command = ["eye", input_file, "--quiet" , "--nope" , "--query", query_file]
            
            # 执行命令
            result = subprocess.run(command, cwd="./", capture_output=True, text=True)
            
            # 检查是否成功
            if result.returncode == 0:
                # print("DEBUG: EYE Reasoner executed successfully!")
                # print(result.stdout)
                # print("DEBUG: EOF")
                return result.stdout
            else:
                print("Error:", result.stderr)
                return None

# 示例调用
# output = run_eye("./ontology/state.n3", "query.n3")

def parse_eye_output(output_content):
    g = Graph()
    g.parse(data=output_content, format="n3")
    
    for subj, pred, obj in g:
        print(f"Subject: {subj}, Predicate: {pred}, Object: {obj}")

# # 示例解析
# if output:
#     parse_eye_output(output)


# 游戏流程
def main():

    # 1. 初始化

    RDF_NIL = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#nil")
    
    #合并除了状态以外的图，这些图是系统级别的
    ontology_n3 = merge_n3_files(
        "./ontology/action.n3", 
        "./ontology/item.n3", 
        "./ontology/event.n3", 
        "./ontology/talent.n3", 
        "./ontology/variable.n3",
        "./ontology/utility.n3",
        "./ontology/upper-onto.n3",
        )
    #print("本体和规则合并结果:", ontology_n3)
    write_to_file(ontology_n3, "ontology.n3")

    # 用于传递参数的图。每次传递完参数重置
    arg_graph = Graph() 
    # 用于存储当前动作的图。每步重置。
    current_action = Graph()

    # 预先从routine文件夹中的每个文件中读取N3 string. 
    current_state_n3 = read_from_file("./routine/init-state.n3")
    update_world_n3 = read_from_file("./routine/update-world.n3")
    query_action_n3 = read_from_file("./routine/query-action.n3")
    query_action_param_n3 = read_from_file("./routine/query-action-param.n3")
    query_action_param_range_n3 = read_from_file("./routine/query-action-param-range.n3")
    query_action_param_message_n3 = read_from_file("./routine/query-action-param-message.n3")
    


    print("新的轮回开始了!\n")
    

    # 2. 循环游戏回合 
    while True:
        

        arg_graph.remove((None, None, None))

        # 2.0 创建世界，构建知识库basen
        
        # 因为没有增量推理，用缓存图cache来存储所有的临时推理结果。
        cache_n3 = eye_inference(current_state_n3, ontology_n3)
        write_to_file(cache_n3, "cache.n3") # DEBUG


        base_n3 = merge_n3(current_state_n3, ontology_n3, cache_n3)
        write_to_file(base_n3, "base.n3") # DEBUG
        

        # 2.1 用户执行动作, 更新世界

        # 2.1.0 获取可执行动作
        answer = eye_query(query_action_n3, base_n3 )
        assert answer is not None, "推理器查询动作失败，无法继续游戏。" # 最少也应该能执行跳过的动作
        available_actions = collect_answers(answer)
        
        while True: # 循环，直到执行了跳过
            current_action.remove((None,None,None))
            if len(available_actions) > 1: # 有除了跳过之外的可选动作
                print("你可以执行的动作有:")
                for idx, action in enumerate(available_actions, 0):
                    #打印动作的简短名称
                    print(f"{idx}. {action.split('#')[-1]}")
                print("\n请选择你要执行的动作（输入数字）:")
                

                while True: # 选择动作的循环
                    selected_action = input()
                    if selected_action.isdigit() and 0 <= int(selected_action) <= len(available_actions)-1:
                        break
                    else:
                        print("无效的选择，请重新输入。")
            else:  
                selected_action = 0
            
            if selected_action == 0 :
                break
                
            action_to_execute = available_actions[int(selected_action)]
            # print(f"DEBUG: 你选择的动作是: {action_to_execute}")
            current_action.add((URIRef("http://semex.sigmanoise.com/r3/life-sim#当前动作"), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), action_to_execute))

            # 2.1.1 如果是有参数的动作，需要进一步输入参数 
            arg_graph.add((URIRef("http://semex.sigmanoise.com/r3/life-sim#arg"), URIRef("http://semex.sigmanoise.com/r3/life-sim#is"), action_to_execute))
            arg_n3 = arg_graph.serialize(format="n3")
            arg_graph.serialize("arg.n3",format="n3")
            
            answer = eye_query(query_action_param_n3, base_n3, arg_n3)
            # print("DEBUG: 动作参数查询结果：",answer)
            params = get_answers(answer)

            if params != RDF_NIL:  #动作有参数
                for param in params:
                    # 构建参数图
                    arg_graph.remove((None, None, None))
                    arg_graph.add((URIRef("http://semex.sigmanoise.com/r3/life-sim#arg"), URIRef("http://semex.sigmanoise.com/r3/life-sim#is"), param))
                    arg_n3 = arg_graph.serialize(format="n3")

                    # 2.1.1.0 如果参数有提示信息，打印信息
                    answer = eye_query(query_action_param_message_n3,base_n3,arg_n3)
                    param_message = get_answers(answer)
                    if param_message:
                        print(f"{param.split('#')[-1]}是？(", param_message, ")")
                    else:
                        print(f"{param.split('#')[-1]}是？")

                    
                    # 2.1.1.1 如果参数的取值范围是列表，需要列出选项
                    answer = eye_query(query_action_param_range_n3, base_n3, arg_n3)
                    param_values = get_answers(answer) #可能是列表或者节点

                    # 如果返回的取值范围是列表：
                    if isinstance(param_values, list):
                        #print("可选项:")
                        for idx, r in enumerate(param_values, 0):
                            r_qname = r.split('#')[-1]
                            print(f"{idx}. {r_qname}")
                        print("请选择（输入数字）:")
                        while True:
                            param_value = input()
                            if param_value.isdigit() and 0 <= int(param_value) <= len(param_values) - 1:
                                param_value = param_values[int(param_value) ]
                                # print(f"DEBUG: 你选择的{param}的参数值是: {param_value}")
                                current_action.add((URIRef("http://semex.sigmanoise.com/r3/life-sim#当前动作"), param, param_value))
                                break
                            else:
                                print("无效的选择，请重新输入。")
                    # 2.1.1.2 取值范围不是列表，直接输入
                    else: 
                        # 提示取值范围。可以用 ?action :取值范围 或 ?action :
                        while True:
                            param_value = input()
                            # 判断用户的输入是字符串还是数值，将相应类型的字面量存储到三元组中。
                            try:
                                # 尝试将输入转换为整数
                                param_value = Literal(int(param_value))
                            except ValueError:
                                try:
                                    # 尝试将输入转换为浮点数
                                    param_value = Literal(float(param_value))
                                except ValueError:
                                    # 如果都失败了，就当作字符串处理
                                    param_value = Literal(param_value)
                            current_action.add((URIRef("http://semex.sigmanoise.com/r3/life-sim#当前动作"), param, param_value))
                            
                            # 2.1.1.2.1  输入参数的合法性检查
                            # TODO 首先检查参数类型是否正确。使用check-action-param.n3，或者合并到action.n3
                            

                            # 然后检查范围是否正确。
                            # 这个临时子图混合base推理中是否有 Failed的实例，即形如 xxx a :Failed 的三元组   
                            check_result = eye_inference(base_n3, current_action.serialize(format="n3"))
                            if check_result:
                                check_graph = Graph()
                                check_graph.parse(data=check_result, format="n3")
                                failed = False
                                for s3, p3, o3 in check_graph.triples((None, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), URIRef("http://semex.sigmanoise.com/r3/life-sim#Failed"))):
                                    failed = True
                                    reason = None
                                    for s4, p4, o4 in check_graph.triples((s3, URIRef("http://semex.sigmanoise.com/r3/life-sim#reason"), None)):
                                        reason = o4
                                    print(f"参数{param.split('#')[-1]}的值有误: {reason}")
                                if failed:
                                    print("请重新输入参数值:")
                                    current_action.remove((URIRef("http://semex.sigmanoise.com/r3/life-sim#当前动作"), param, Literal(param_value)))
                                    
                                else:
                                    print(f"{param.split('#')[-1]}的值是: {param_value}")
                                    break

            # 2.1.2 根据用户动作及其参数，执行推理，更新世界状态
            current_action_n3 = current_action.serialize(format="n3")
            # action_outcomes = eye_inference(current_state_n3, ontology_n3, current_action_n3) # 不包括cache的部分？
            action_outcomes_n3 = eye_inference(base_n3, current_action_n3)
            print("DEBUG: 动作效果是", action_outcomes_n3)
        

            if action_outcomes_n3.strip(): #动作有结果
                write_to_file(action_outcomes_n3,"action-outcomes.n3")
                write_to_file(current_state_n3,"current-state.n3")
            
                # 执行update-world.n3中的规则，生成新的世界状态 
                next_state_n3 = eye_inference(action_outcomes_n3, current_state_n3, update_world_n3)
                print("DEBUG: 世界已更新！ 你当前的状态是：", next_state_n3)
            else:
                pass
                print("动作无效果!")
        
        # 2.2 根据状态， 生成新事件

            # 2.2.1 找到所有可能发生的、最细粒度的事件

            # 2.2.2 计算事件的后果并更新世界

        # 

                


        

            


                

                    
            

            
        break


  


    return

if __name__ == "__main__":
    main()