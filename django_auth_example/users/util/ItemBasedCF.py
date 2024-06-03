import sys
import random
import math
from operator import itemgetter
import os
import statistics

random.seed(0)
matrix = []
matrix2 = []
current_path_ = os.getcwd()
file_path = '../data/users_resulttable.csv'
model_path = 'item_cf_train.model'

class ItemBasedCF(object):
    u2m_rating_trainset = {}  # 训练集
    m2u_rating_trainset = {}
    u2m_rating_testset = {}  # 测试集
    n_sim_item = 20  # 相似用户数量
    n_rec_movie = 20  # 在这里修改推荐电影数量

    movie_count = 0  # 总电影数量
    item_sim_mat = {}

    def __init__(self):
        self.u2m_rating_trainset = {}  # 训练集
        self.u2m_rating_testset = {}  # 测试集
        self.m2u_rating_trainset = {}
        self.n_sim_item = 20  # 相似用户数量
        self.n_rec_movie = 20  # 在这里修改推荐电影数量

        self.movie_count = 0  # 总电影数量

    @staticmethod
    def loadfile(filename):
        """
        :param filename:load a file
        :return:a generator
        """
        fp = open(filename, 'r', encoding='UTF-8')
        for i, line in enumerate(fp):
            yield line.strip('\r\n')
        fp.close()
        print('加载 %s 成功' % filename, file=sys.stderr)

    def train(self, filename2, pivot=1.0):
        train_data_size = 0
        test_data_size = 0
        for line in self.loadfile(filename2):
            user, movie, rating = line.split(',')
            user = int(user)
            movie = int(movie)
            rating = float(rating)
            if random.randint(0, 101) < pivot * 100:
                self.u2m_rating_trainset.setdefault(user, {})
                self.u2m_rating_trainset[user][movie] = rating
                train_data_size += 1
            else:
                self.u2m_rating_testset.setdefault(user, {})
                self.u2m_rating_testset[user][movie] = rating
                test_data_size += 1
        print(f"成功拆分测试集和训练集{train_data_size}:{test_data_size}")
        self.m2u_rating_trainset = {}
        for user, movies in self.u2m_rating_trainset.items():
            for movie in movies.keys():
                rating = self.u2m_rating_trainset[user][movie]
                if movie not in self.m2u_rating_trainset.keys():
                    self.m2u_rating_trainset[movie] = {}
                self.m2u_rating_trainset[movie][user] = rating
        self.movie_count = len(self.m2u_rating_trainset)
        print(f"完成构建电影评分倒排索引，共有{self.movie_count}部电影")
        
    def calc_sim_items(self, item_id):
        if item_id not in self.m2u_rating_trainset.keys():
            return {}
        item_user_rating_dict = self.m2u_rating_trainset[item_id]
        sim_items_dict = {}
        for user_id in item_user_rating_dict.keys():
            if user_id in self.u2m_rating_trainset.keys():
                for other_item_id in self.u2m_rating_trainset[user_id].keys():
                    if other_item_id!=item_id and not other_item_id in self.item_sim_mat.keys():
                        other_item_user_rating_dict = self.m2u_rating_trainset[other_item_id]
                        similarity = self.cos_sim(item_user_rating_dict, other_item_user_rating_dict)
                        sim_items_dict[other_item_id] = similarity
        return self.sort_dict_by_value_and_get_top_n(sim_items_dict, self.n_sim_item)


    def sort_dict_by_value_and_get_top_n(self, d, n=20):
        # 对字典的项进行排序，根据值从大到小
        sorted_items = sorted(d.items(), key=lambda item: item[1], reverse=True)
        
        # 选择最大的n个键值对，如果字典中的项少于n个，则选择所有项
        top_n_items = sorted_items[:n]
        
        # 将选定的键值对转换回字典
        result_dict = dict(top_n_items)
        
        return result_dict
    
    def cos_sim(self, rating_dict1, rating_dict2):
        sqrt1 = math.sqrt(sum([rating * rating for rating in rating_dict1.values()]))
        sqrt2 = math.sqrt(sum([rating * rating for rating in rating_dict2.values()]))
        sim_sum = 0.0
        for item_id in rating_dict1.keys():
            if item_id in rating_dict2.keys():
                sim_sum += rating_dict1[item_id] * rating_dict2[item_id]
        return sim_sum/(sqrt1 * sqrt2)

    # 排序推荐方法
    def recommend(self, item_rating_dict, topN=20, exclude_rated_items=True):
        rec_item_dict = {}
        for item_id in item_rating_dict.keys():
            item_rating = item_rating_dict[item_id]
            sim_items_dict = self.calc_sim_items(item_id)
            for sim_item_id in sim_items_dict.keys():
                similarity = sim_items_dict[sim_item_id]
                if exclude_rated_items and sim_item_id in item_rating_dict.keys():
                    continue
                else:
                    if sim_item_id not in rec_item_dict.keys():
                        rec_item_dict[sim_item_id] = [item_rating * similarity, similarity]
                    else:
                        rec_item_dict[sim_item_id] = [rec_item_dict[sim_item_id][0] + item_rating * similarity, 
                                                            rec_item_dict[sim_item_id][1] + similarity]
        for rec_item_id in rec_item_dict.keys():
            rec_item_dict[rec_item_id] = round(rec_item_dict[rec_item_id][0] / rec_item_dict[rec_item_id][1], 2)
        return self.sort_dict_by_value_and_get_top_n(rec_item_dict, topN)
    
    def evaluate(self, topN=20):
        mae = 0.0
        rmse = 0.0
        rec_count = 0
        abs_error = 0.0
        abs_error_square = 0.0

        for uid in list(self.u2m_rating_testset.keys())[0:50]:
            rating_dict = self.u2m_rating_testset[uid]
            user_mean_rating = statistics.mean(list(rating_dict.values()))
            rec_result_dict = self.recommend(rating_dict, topN=topN, exclude_rated_items=False)
            for rec_item_id in rec_result_dict:
                if rec_item_id in rating_dict.keys():
                    rec_count += 1
                    abs_error += abs(rec_result_dict[rec_item_id] - rating_dict[rec_item_id])
                    abs_error_square += abs(rec_result_dict[rec_item_id] - rating_dict[rec_item_id]) ** 2
                else:
                    rec_count += 1
                    abs_error += abs(rec_result_dict[rec_item_id] - user_mean_rating)
                    abs_error_square += abs(rec_result_dict[rec_item_id] - user_mean_rating) ** 2
        
        mae = abs_error / rec_count
        rmse = math.sqrt(abs_error_square / rec_count)

        print(f"基于{self.n_sim_item}相似物品的top{topN}评估:评估推荐数量{rec_count}, MAE={mae}, RMSE={rmse}")


if __name__ == '__main__':
    ibcf = ItemBasedCF()
    ibcf.train(file_path, pivot=0.8)
    sample_iid = list(ibcf.m2u_rating_trainset.keys())[0]
    sim_items_dict = ibcf.calc_sim_items(sample_iid)
    print(f"物品{sample_iid}的相似物品有:{sim_items_dict}")

    uid = list(ibcf.u2m_rating_testset.keys())[0]
    rating_dict = ibcf.u2m_rating_testset[uid]
    rec_item_dict = ibcf.recommend(rating_dict, topN=20)
    print(f"用户{uid}的推荐电影:{rec_item_dict}")

    ibcf.evaluate()