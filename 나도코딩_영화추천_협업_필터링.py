# -*- coding: utf-8 -*-
"""나도코딩-영화추천-협업 필터링

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pLRN9kvNBtMu6Y5AMr75yoqjIAXZNDHd

# **환경설정**
"""

# Collaborative Filtering (협업 필터링 : 사용자 리뷰 기반)

"""예) 사람1본영화: up,주토피아
사람2본영화 : up,주토피아,인사이드 아웃

사람1에게 인사이드 아웃을 추천
"""

pip install scikit-surprise

import surprise 
surprise.__version__

import pandas as pd
from surprise import Reader,Dataset,SVD
from surprise.model_selection import cross_validate

import pandas as pd
from surprise import Reader
from surprise import Dataset
from surprise.model_selection import cross_validate
from surprise import NormalPredictor
from surprise import KNNBasic
from surprise import KNNWithMeans
from surprise import KNNWithZScore
from surprise import KNNBaseline
from surprise import SVD
from surprise import BaselineOnly
from surprise import SVDpp
from surprise import NMF
from surprise import SlopeOne
from surprise import CoClustering
from surprise.accuracy import rmse
from surprise import accuracy
from surprise.model_selection import train_test_split

df = pd.read_csv('ratings_small.csv')
df.head()

df.shape

df.info

"""# **EDA**

Ratings Distribution
"""

from plotly.offline import init_notebook_mode, plot,iplot
import plotly.graph_objs as go
init_notebook_mode(connected=True)

data2 = df['rating'].value_counts().sort_index(ascending=False)
trace = go.Bar(x=data2.index,
               text=['{:.1f}%'.format(val) for val in (data2.values/df.shape[0]*100)],
               textposition='auto',
               textfont = dict(color='#000000'),
               y=data2.values,
               )

layout = dict(title='Distribution of {} movies-ratings'.format(df.shape[0]),
              xaxis=dict(title='Rating'),
              yaxis=dict(title='Count'))

data2

fig = go.Figure(data=trace,layout=layout) 
# iplot(fig)
fig.show(renderer='colab')

"""x: 평가 점수 

y: 평가점수 분포 %

**Ratings Distribution by movie**
"""

data = df.groupby('movieId')['rating'].count().clip(upper=50)
# movieId를 그룹화 한다 
# movieId를 그룹 마다 rating 값을 센다 (rating 값 개수세기, 더하는 것은 아님)
# clip(upper=50) -> 50은 상한값입니다. 50 이상의 값은 50으로 변경됩니다.

trace = go.Histogram(x=data.values,
                     name='Ratings',
                     xbins=dict(start=0,
                               end=50,
                               size=2))

layout = go.Layout(title='Distribution of Number of Ratings Per Movie(Clipped at 50)',
                   xaxis=dict(title='Number of Ratings Per Movie'),
                   yaxis=dict(title='Count'),
                   bargap=0.2)

fig = go.Figure(data=[trace],layout=layout)
fig.show(renderer='colab')

"""5개 이하의 평가를 받은 영화들이 대부분이다.

y: 영화수


x : 영화가 받은 투표수 (50개 이상 투표받은 영화는 하나로 50으로 통일)
"""

df.groupby('movieId')['rating'].count().reset_index().sort_values('rating',
                                                               ascending=False)[:10]

"""가장 많은 평가를 기록한 영화(Id=356)는 341개의 평가를 받았다

**Ratings Distribution By User**
"""

data = df.groupby('userId')['movieId'].count().clip(upper=50)

trace = go.Histogram(x=data.values,
                     name='Ratings',
                     xbins=dict(start=0,
                                end=50,
                                size=2))

layout = go.Layout(title='Distribution of Number of ratings per user(clipped at 50)',
                   xaxis = dict(title='Ratings per user'),
                   yaxis = dict(title='Count'),
                   bargap=0.2)

fig = go.Figure(data=[trace],layout=layout)
fig.show(renderer='colab')

df.groupby('userId')['rating'].count().reset_index().sort_values('rating',ascending=False)[:10]

"""가장 많이 평가를 한 userId=547 은 2391개의 평가를 했으며, 평가 수가 저조한 user도 있다는 것을 알 수 있다.

# **데이터 전처리 | 평가 수가 저조한 영화와 유저를 제외 시키다**

50이상은 날려야 한다라는 기준을 정한 것에 대한 근거가 부족
"""

min_movies_ratings = 50
filter_movies = df['movieId'].value_counts()>min_movies_ratings
filter_movies = filter_movies[filter_movies].index.tolist()

# 50개 보다 많은 평가를 기록한 영화만을 필터링

len(filter_movies)

a=df['movieId'].unique()
a=a.tolist()
len(a)

df['movieId'].nunique()

min_user_ratings = 50
filter_users = df['userId'].value_counts() > min_user_ratings
filter_users = filter_users[filter_users].index.tolist()

# 50개 보다 많은 평가를 기록한 유저만을 필터링

df_new = df[(df['movieId'].isin(filter_movies)) & (df['userId'].isin(filter_users))]

print('The original data frame shape : \t{}'.format(df.shape))
print('The new data frame shape : \t{}'.format(df_new.shape))

"""# **Surprise 를 위한 전처리**

load_from_df() 메소드 ->  panda 데이터프레임으로부터 데이터셋을 로딩하기 위해서

Reader object 가 필요하고, rating_scale 파라메터가 특정

데이터 프레임은 사용자 id, 아이템 id, 평가에 대응하는 3개의 컬럼을 가지고 있어야 한다.
"""

df_new['rating'].min()

df_new['rating'].max()

reader = Reader(rating_scale=(0.5,5)) 
#rating_scale defalt 값이 1,5 였기 때문에 scale을 조정해줌

data = Dataset.load_from_df(df_new[['userId','movieId','rating']],reader=reader)
# surprise 에서는 ['userId','movieId','rating'] 형식을 지원한다
data

"""# **모델 선택**

교차검증

정확도 척도 : RMSE 왜?
"""

benchmark = []

for algorithm in [SVD(),SVDpp(),SlopeOne(),NMF(),NormalPredictor(), KNNBaseline(), KNNBasic(), KNNWithMeans(), KNNWithZScore(), BaselineOnly(), CoClustering()]:
  results = cross_validate(algorithm,data,measures=['RMSE'],cv=3,verbose=False)

  # 결과 얻기 & 알고리즘 이름을 저장
  tmp = pd.DataFrame.from_dict(results).mean(axis=0)
  tmp = tmp.append(pd.Series([str(algorithm).split(' ')[0].split('.')[-1]],index=['Algorithm']))
  benchmark.append(tmp)

pd.DataFrame(benchmark).set_index('Algorithm').sort_values('test_rmse')

"""# **SVDpp**

SVDpp 알고리즘이 가장 좋은 rmse결과를 보였다. 


따라서 SVDpp를 사용하여 훈련 및 예측을 진행하고 교대최소제곱(Alternating Least Squares,ALS) 을 사용할 것이다
"""

surprise_results = pd.DataFrame(benchmark).set_index('Algorithm').sort_values('test_rmse')

print('Using SVDpp')
# bsl_options = {'method' : 'als'}
algo = SVDpp()
cross_validate(algo,data,measures=['RMSE'],cv=3,verbose=False)

trainset = data.build_full_trainset()

algo.fit(trainset)

df_new[df_new['userId']==2]

algo.predict(2,39,5) 
# userId=1 , movieId=1029
#r_ui : 해당 영화 실제 평가 점수
# est : 해당 영화를 평가할 것으로 예측되는 점수

"""# **SVD**"""

svd = SVD(random_state=0)
cross_validate(svd,data,measures=['RMSE','MAE'],cv=5,verbose=True)

svd.fit(trainset)

svd.predict(2,39,5)

"""# **bsl**"""

print('Using ALS')
bsl_options = {'method': 'als',
               'n_epochs': 5,
               'reg_u': 12,
               'reg_i': 5
               }
bsl = BaselineOnly(bsl_options=bsl_options)
cross_validate(bsl, data, measures=['RMSE'], cv=3, verbose=False)

bsl.fit(trainset)

bsl.predict(2,39,5)

"""# **전처리 하지 않은 SVDpp**"""

data_old = Dataset.load_from_df(df[['userId','movieId','rating']],reader=reader)
# surprise 에서는 ['userId','movieId','rating'] 형식을 지원한다

trainset_old = data_old.build_full_trainset()

svd.fit(trainset_old)

bsl.fit(trainset_old)

bsl.predict(1,2294,2)

svd.predict(1,1339,3.5)

df[df['userId']==1]