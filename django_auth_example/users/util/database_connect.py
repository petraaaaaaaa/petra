
import sys
import pymysql
import csv
import codecs

from django.shortcuts import render
from django.http import JsonResponse

sys.path.append(r'../forms.py')
from users.models import Resulttable, Insertposter


# # 向数据库中插入评分数据
# def insert(request):
#     global USERID
#     USERID = int(request.GET.get('userId')) + 1000
#     RATING = float(request.GET.get("rating"))
#     IMDBID = int(request.GET.get("imdbId"))
#     Resulttable.objects.create(userId=USERID, rating=RATING, imdbId=IMDBID)
#     return render(request, 'index.html')

# 向数据库中插入评分数据
def insert(request) -> JsonResponse:
    global USERID
    USERID = int(request.GET.get('userId')) + 1000
    RATING = float(request.GET.get("rating"))
    IMDBID = int(request.GET.get("imdbId"))
    execute_sql_with_commit(f"delete from users_resulttable where userId={USERID} and imdbId={IMDBID}")
    execute_sql_with_commit(f"insert into users_resulttable (userId, imdbId, rating) values ({USERID},{IMDBID},{RATING})")
    data = {'result':'success'}
    return JsonResponse(data)


# 连接数据库的方法
def get_conn():
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        passwd='123456',
        db='test_moviedata',
        charset='utf8')
    return conn


# 执行sql语句
def query_all(cur, sql, args):
    cur.execute(sql, args)
    return cur.fetchall()

# 执行sql语句
def execute_sql(sql):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

# 执行sql语句
def execute_sql_with_commit(sql):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

def read_mysql_to_csv(filename, userid):
    """
    从mysql中读取数据到csv方便下次使用
    :param filename:需要写入的csv
    :param user:从数据库中读取的user的评分
    :return:无
    """
    with codecs.open(filename=filename, mode='w', encoding='utf-8') as f:
        write = csv.writer(f, dialect='excel')
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('select * from users_resulttable')
        rr = cur.fetchall()  # 返回多个元组，即返回多个记录(rows),如果没有结果返回()
        for result in rr:
            write.writerow(result[:-1])


def read_mysql_to_csv2(filename, user):
    with codecs.open(filename=filename, mode='a', encoding='utf-8') as f:
        write = csv.writer(f, dialect='excel')
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('select * from users_resulttable')
        sql = ('select * from users_resulttable WHERE userId = 1001')
        rr = cur.fetchall()
        results = query_all(cur=cur, sql=sql, args=None)
        for result in results:
            # print(result)
            write.writerow(result[:-1])
