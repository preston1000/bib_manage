SYNONYMS = {"导览": ["导览", "参观", "看看", "转转", "导览", "访问", "观光", "游览", "视察", "考察", '看', '看一下'],
            "欢迎": ["欢迎", "接待", "迎宾", '接', '迎接'],
            "讲解": ["讲解", "讲", "介绍", "解说", "说明", "诠释"],
            "送别": ["送别", "欢送", "送行", "再见", "告别", '送', '送到'],
            # "递送": ["递送", '拿', '给'],
            "停止": ["停止", "停", "停下来", "停一下", "暂停", "不要讲"]
            # "充电": ["充电", "返充"],
            # "指": ["指", "指路", "指向"],
            # "看": ["看", "看向", "盯着", "望着", "看着"],
            # "互动": ["互动", "玩", "交流", "沟通"],
            # "跳舞": ["跳舞", "舞蹈", "跳个舞"]
            }
POSSIBILITY = {'介绍': 0.9, '给': 0.1}


SYNONYMS_INVERSE = {}
WORDS = []
for key, value in SYNONYMS.items():
    WORDS.append(list(value))

for i in range(len(WORDS)):
    for j in range(len(WORDS[i])):
        word = WORDS[i][j]
        index = SYNONYMS_INVERSE.get(word, None)
        if index:
            SYNONYMS_INVERSE[word] = SYNONYMS_INVERSE[word].append(WORDS[i][0])
        else:
            SYNONYMS_INVERSE[word] = [WORDS[i][0]]
WORDS = list(SYNONYMS_INVERSE.keys())
