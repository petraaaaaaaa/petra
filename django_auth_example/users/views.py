import os
from django.shortcuts import render, redirect
from concurrent.futures import ThreadPoolExecutor
from users.util.ItemBasedCF import *
from users.util.LFM import *
from users.util.UserBasedCF import *
from users.util.database_connect import *
from .forms import RegisterForm
from users.models import Resulttable, Insertposter
from users.util.item_info import item_dict

lfm = LFM(train_size=0.8, ratio=1)
lfm.load()

ubcf = UserBasedCF()
ubcf.train(file_path, pivot=1.0)

ibcf = ItemBasedCF()
ibcf.train(file_path, pivot=1.0)


# 注册方法
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/users/login')
    else:
        form = RegisterForm()

    return render(request, '../templates/users/register.html', context={'form': form})


def index(request):
    return render(request, 'users/..//index.html')


def check(request):
    return render(request, 'users/..//index.html')


# 用于展示用户评过的电影
def showmessage(request):
    user_movie_ratings = []
    userid = int(request.GET.get('userIdd')) + 1000
    data = Resulttable.objects.filter(userId=userid)
    for row in data:
        rating_dict = {}
        rating_dict['movie_id'] = row.imdbId
        rating_dict['rating'] = float(row.rating)
        rating_dict['movie_name'] = item_dict.get_item_info_by_item_id(row.imdbId).item_name
        user_movie_ratings.append(rating_dict)

    return render(request, 'users/message.html', locals())


def recommend1(request):
    USERID = int(request.GET.get("userIdd")) + 1000
    user_items_rating = execute_sql(f"SELECT * FROM users_resulttable where userId={USERID}")
    rating_dict = {item_rating[2]: float(item_rating[3]) for item_rating in user_items_rating}

    def get_lfm_recommendations(rating_dict):
        rec_results = lfm.recommend(rating_dict, 20)
        return item_dict.get_item_info_by_item_ids([rec_result[0] for rec_result in rec_results])

    def get_ubcf_recommendations(rating_dict):
        rec_results = ubcf.recommend(rating_dict)
        return item_dict.get_item_info_by_item_ids([key for key in rec_results.keys()])

    def get_ibcf_recommendations(rating_dict):
        rec_results = ibcf.recommend(rating_dict)
        return item_dict.get_item_info_by_item_ids([key for key in rec_results.keys()])

    with ThreadPoolExecutor() as executor:
        lfm_future = executor.submit(get_lfm_recommendations, rating_dict)
        ubcf_future = executor.submit(get_ubcf_recommendations, rating_dict)
        ibcf_future = executor.submit(get_ibcf_recommendations, rating_dict)

        lfm_rec_results = lfm_future.result()
        ubcf_rec_results = ubcf_future.result()
        ibcf_rec_results = ibcf_future.result()

    return render(request, 'users/movieRecommend.html', locals())


def recommend2(request):
    USERID = int(request.GET.get('userIdd')) + 1000
    read_mysql_to_csv2('users/static/users_resulttable2.csv', USERID)
    ratingfile2 = os.path.join('users/static', 'users_resulttable2.csv')
    itemcf = ItemBasedCF()
    userid = str(USERID)
    itemcf.generate_dataset(ratingfile2)
    itemcf.calc_movie_sim()
    itemcf.recommend(userid)

    try:
        conn = get_conn()
        cur = conn.cursor()
        for i in matrix2:
            cur.execute('select * from users_resulttable where imdbId = %s', i)
            rr = cur.fetchall()
            for imdbId, title, poster in rr:
                if not Insertposter.objects.filter(title=title).exists():
                    Insertposter.objects.create(userId=USERID, title=title, poster=poster)
    finally:
        conn.close()

    results = Insertposter.objects.filter(userId=USERID)
    return render(request, 'users/movieRecommend2.html', locals())


if __name__ == '__main__':
    ratingfile2 = os.path.join('static', 'users_resulttable.csv')
    usercf = UserBasedCF()
    userId = '1'
    usercf.generate_dataset(ratingfile2)
    usercf.calc_user_sim()
    usercf.recommend(userId)
