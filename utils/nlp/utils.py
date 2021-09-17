
from pathlib import Path

from utils.ddparser import DDParser
from LAC import LAC

basedir = Path(__file__).parent.parent.parent  # 项目根目录
current_dir = Path(__file__).parent  # 当前文件夹
"""
分词/依存关系配置
"""
lac_dict_path = basedir.joinpath('model_files/LAC_dict/tokenize_dict_lac.txt')
dd_parser_model_path = basedir.joinpath('model_files/ddparser_models')

lac = LAC()
lac.load_customization(lac_dict_path)
ddp = DDParser(use_cuda=False, tree=True, prob=False, use_pos=False, model_files_path=dd_parser_model_path, buckets=False,
               batch_size=None, encoding_model="ernie-lstm")


def dd_parser_caller(sentence):
    """
    获取给定句子的依存关系
    :param sentence: str
    :return: tokens (list of str), head (list of str, words), deprel (list of str)
    """
    lac_result = lac.run(sentence)
    dep_result = ddp.parse_seg(lac_result)

    pos_tag = dep_result[1].get("word", None)
    tokens = dep_result[0].get("word", None)
    head_integer = dep_result[0].get("head", None)
    dep_rel = dep_result[0].get("deprel", None)

    head = []

    for i in range(len(tokens)):
        if head_integer[i] == 0:
            head.append("Root")
        else:
            head.append(tokens[head_integer[i]-1])

    return tokens, head, dep_rel, pos_tag