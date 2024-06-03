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
model_path = 'user_cf_train.model'

class UserBasedCF(object):
    """
    类UserBasedCF
    基于用户的协同过滤算法--推荐算法
    """
    u2m_rating_trainset = {}  # 训练集
    m2u_rating_trainset = {}
    u2m_rating_testset = {}  # 测试集
    initialset = {}  # 存储要推荐的用户的信息
    n_sim_user = 20  # 相似用户数量
    n_rec_movie = 20  # 在这里修改推荐电影数量

    movie_popular = {}
    movie_count = 0  # 总电影数量
    user_sim_mat = {}

    def __init__(self):
        self.u2m_rating_trainset = {}  # 训练集
        self.u2m_rating_testset = {}  # 测试集
        self.m2u_rating_trainset = {}
        self.n_sim_user = 20  # 相似用户数量
        self.n_rec_movie = 20  # 在这里修改推荐电影数量

        self.movie_popular = {}
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
                if movie not in self.m2u_rating_trainset.keys():
                    self.m2u_rating_trainset[movie] = set()
                self.m2u_rating_trainset[movie].add(user)
                if movie not in self.movie_popular:
                    self.movie_popular[movie] = 0
                self.movie_popular[movie] += 1
        self.movie_count = len(self.m2u_rating_trainset)
        print(f"完成构建电影评分倒排索引，共有{self.movie_count}部电影")
        
    def calc_user_sim(self, item_rating_dict, n=20):
        sim_users_dict = {}
        for item_id in item_rating_dict.keys():
            if item_id in self.m2u_rating_trainset.keys():
                for other_user_id in self.m2u_rating_trainset[item_id]:
                    if not other_user_id in sim_users_dict.keys():
                        other_user_item_rating_dict = self.u2m_rating_trainset[other_user_id]
                        similarity = self.cos_sim(item_rating_dict, other_user_item_rating_dict)
                        sim_users_dict[other_user_id] = similarity
        return self.sort_dict_by_value_and_get_top_n(sim_users_dict, n)

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
    def recommend(self, item_rating_dict, sim_user_count=20, topN=20, exclude_rated_items=True):
        sim_users_dict = self.calc_user_sim(item_rating_dict, sim_user_count)
        rec_item_dict = {}
        for sim_user_id in sim_users_dict.keys():
            similarity = sim_users_dict[sim_user_id]
            sim_user_item_rating_dict = self.u2m_rating_trainset[sim_user_id]
            for other_item_id in sim_user_item_rating_dict.keys():
                other_item_rating = sim_user_item_rating_dict[other_item_id]
                if exclude_rated_items and other_item_id in item_rating_dict.keys():
                    continue
                else:
                    if not other_item_id in item_rating_dict.keys():
                        if not other_item_id in rec_item_dict.keys():
                            rec_item_dict[other_item_id] = [other_item_rating * similarity, similarity]
                        else:
                            rec_item_dict[other_item_id] = [
                                rec_item_dict[other_item_id][0] + other_item_rating * similarity,
                                rec_item_dict[other_item_id][1] + similarity
                            ]
        for rec_item_id in rec_item_dict.keys():
            rec_item_dict[rec_item_id] = round(rec_item_dict[rec_item_id][0] / rec_item_dict[rec_item_id][1], 2)
        return self.sort_dict_by_value_and_get_top_n(rec_item_dict, topN)
    
    def evaluate(self, sim_user_count=20, topN=20):
        mae = 0.0
        rmse = 0.0
        rec_count = 0
        abs_error = 0.0
        abs_error_square = 0.0

        for uid in self.u2m_rating_testset.keys():
            rating_dict = self.u2m_rating_testset[uid]
            user_mean_rating = statistics.mean(list(rating_dict.values()))
            rec_result_dict = self.recommend(rating_dict, sim_user_count=sim_user_count, topN=topN, exclude_rated_items=False)
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

        print(f"基于{sim_user_count}相似用户的top{topN}评估:评估推荐数量{rec_count}, MAE={mae}, RMSE={rmse}")


if __name__ == '__main__':
    ubcf = UserBasedCF()
    ubcf.train(file_path, pivot=0.8)
    uid = list(ubcf.u2m_rating_testset.keys())[0]
    rating_dict = ubcf.u2m_rating_testset[uid]
    sim_user_dict = ubcf.calc_user_sim(rating_dict, n=20)
    print(f"用户{uid}的相似用户:{sim_user_dict}")
    rec_item_dict = ubcf.recommend(rating_dict, topN=20)
    print(f"用户{uid}的推荐电影:{rec_item_dict}")

    ubcf.evaluate(sim_user_count=20, topN=20)
