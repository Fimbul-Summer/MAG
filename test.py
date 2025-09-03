import tempfile
import subprocess

def read_from_file(file_path):
    '''从文件读取字符串'''
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def eye_inference(*n3_strings):
    '''运行EYE推理器，返回推理结果. 输入是n3字符串，输出也是n3字符串'''


    # 将n3strings写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        for n3 in n3_strings:
            temp_file.write(n3 + "\n")
        temp_file.flush()
        temp_file.seek(0)
        input_file = temp_file.name
        print(input_file)


        command = ["eye", input_file, "--quiet", "--nope", "--pass-only-new"]
        
        # 执行命令
        # cwd="/Users/Shared/code/人生重开模拟器"
        result = subprocess.run(command, cwd="/Users/Shared/code/人生重开模拟器", capture_output=True, text=True)
        
        # 检查是否成功
        if result.returncode == 0:
            #print("DEBUG: EYE Reasoner executed successfully!")
            #print(read_from_file(input_file))
            #print(result.stdout)
            return result.stdout
        else:
            print("Error:", result.stderr)
            return None


test_n3 = read_from_file("test.n3")
output = eye_inference(test_n3)
print(output)