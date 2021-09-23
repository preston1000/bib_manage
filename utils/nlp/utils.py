
from pathlib import Path

from utils.ddparser import DDParser
from LAC import LAC

from graphviz import Digraph

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


def get_modifier_as_children_att(word, words, head, dep_rel):
    """
    识别一个词之前的定语，如一杯水、一号展厅门口。暂时只能识别定语词，无法识别从句
    :param word:
    :param words:
    :param head:
    :param dep_rel:
    :return:
    """
    modifier = ""
    father = word
    while True:
        att = [ii for ii, tmp_head in enumerate(head) if tmp_head == father and dep_rel[ii] == "ATT"]
        if att:
            if len(att) > 1:
                print('more than one child in <get_modifier_as_children_att>')
            modifier = words[att[0]] + modifier
        else:
            break
        father = words[att[0]]

    if modifier == "":
        modifier = None
    return modifier


def generate_dep_rel_graph(folder, graph_name, words, relation, head, arguments=None):
    """
    生成依存关系图
    :param folder: str
    :param graph_name: str
    :param words: list of str
    :param relation: list of str
    :param head: list of str
    :param arguments: dict
    :return:
    """

    if arguments is None:
        arguments = {}
    graph_format = arguments.get('graph_format', 'png')
    root_name = arguments.get('root_name', 'Root')
    font_name = arguments.get('font_name', "Microsoft YaHei")
    graph_view = arguments.get('graph_view', False)
    graph_cleanup = arguments.get('graph_cleanup', True)

    g = Digraph(graph_name, format=graph_format)
    g.node(name=root_name)
    for word in words:
        g.node(name=word, fontname=font_name)

    for i in range(len(words)):
        if relation[i] not in ['HED']:
            g.edge(words[i], head[i], label=relation[i], fontname=font_name)
        else:
            if head[i] == root_name:
                g.edge(words[i], root_name, label=relation[i], fontname=font_name)
            else:
                g.edge(head[i], root_name, label=relation[i], fontname=font_name)

    try:
        g.render(graph_name, folder, view=graph_view, cleanup=graph_cleanup)
    except RuntimeError:
        g = None
    return g