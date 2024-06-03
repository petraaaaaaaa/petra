import os
import pandas as pd
from typing import List
current_path_ = os.getcwd()
print(f"current_path_:{current_path_}")
# file_path = './users/static/users_resulttable2.csv'
file_path = '../data/MovieGenre3.csv'

class ItemInfo(object):
    item_id: int
    item_name: str
    img_url: str
    def __init__(self, item_id, item_name, img_url):
        self.item_id = item_id
        self.item_name = item_name
        self.img_url = img_url

class ItemDict(object):
    item_dict = {}
    def __init__(self):
        input_data = pd.read_csv(file_path, usecols=range(3))
        input_data.columns = ['item_id', 'item_name', 'img_url']  

        self.item_dict = {}
        for index, row in input_data.iterrows():
            item_id = int(row['item_id'])
            item_name = str(row['item_name'])
            img_url = str(row['img_url'])
            item_info = ItemInfo(item_id, item_name, img_url)
            self.item_dict[item_id] = item_info

    def get_item_info_by_item_id(self, item_id:int) -> ItemInfo:
        if item_id in self.item_dict.keys():
            return self.item_dict[item_id]
        else:
            return None
    
    def get_item_info_by_item_ids(self, item_ids:List[int]) -> List[ItemInfo]:
        ret_list = []
        for item_id in item_ids:
            cur_item_info = self.get_item_info_by_item_id(item_id)
            if cur_item_info:
                ret_list.append(cur_item_info)
        return ret_list

item_dict = ItemDict()