















from scipy import sparse
from sklearn import cross_validation
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble.bagging import BaggingClassifier, BaggingRegressor
from sklearn.ensemble.forest import ExtraTreesClassifier, ExtraTreesRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble.gradient_boosting import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.ensemble.voting_classifier import VotingClassifier
from sklearn.externals import joblib
from sklearn.linear_model import LinearRegression, LogisticRegression, LogisticRegressionCV
from sklearn.linear_model.coordinate_descent import ElasticNetCV, LassoCV
from sklearn.linear_model.ridge import RidgeCV, RidgeClassifier, RidgeClassifierCV
from sklearn.linear_model.stochastic_gradient import SGDClassifier, SGDRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.preprocessing import Binarizer, FunctionTransformer, Imputer, LabelBinarizer, LabelEncoder, MaxAbsScaler, MinMaxScaler, OneHotEncoder, RobustScaler, StandardScaler
from sklearn.svm import LinearSVR, NuSVC, NuSVR, OneClassSVM, SVC, SVR
from sklearn_pandas import DataFrameMapper
from sklearn2pmml.decoration import CategoricalDomain, ContinuousDomain
from pandas import DataFrame
#from xgboost.sklearn import XGBClassifier, XGBRegressor

# for randomSearchCV
from time import time
from operator import itemgetter
from scipy.stats import randint as sp_randint
from sklearn.grid_search import GridSearchCV, RandomizedSearchCV

import numpy
import pandas



SEED = 42  # always use a seed for randomized procedures

def load_csv(name):
	return pandas.read_csv("data/" + name, na_values = ["N/A", "NA"])

def store_csv(df, name):
	df.to_csv("csv/" + name, index = False)

def store_pkl(obj, name):
	joblib.dump(obj, "pkl/" + name, compress = 9)

def mape(sample_y, preds): 
    #y_true, y_pred = check_array(y_true, y_pred)
    return numpy.mean(numpy.abs((sample_y - preds) / sample_y)) * 100

# Utility function to report best scores
def report(grid_scores, n_top=3):
    top_scores = sorted(grid_scores, key=itemgetter(1), reverse=True)[:n_top]
    for i, score in enumerate(top_scores):
        print("Model with rank: {0}".format(i + 1))
        print("Mean validation score: {0:.3f} (std: {1:.3f})".format(
              score.mean_validation_score,
              numpy.std(score.cv_validation_scores)))
        print("Parameters: {0}".format(score.parameters))
        print("")



def build_sample(regressor, name):

	# print estimator.get_params().keys() : specify parameters and distributions to sample from
	param_dist = {"max_depth": [3, None],
		      "max_features": sp_randint(1, 11),
		      "min_samples_split": sp_randint(1, 11),
		      "min_samples_leaf": sp_randint(1, 11)}#,
		      #"bootstrap": [True, False],
		      #"criterion": ["mse", "entropy"]}

	

	# run randomized search
	n_iter_search = 20
	random_search = RandomizedSearchCV(regressor, param_distributions=param_dist,
		                           n_iter=n_iter_search)
	
	# time...
	start = time()
	# repeat the CV procedure 10 times to get more precise results
	n = 10  
	# for each iteration, randomly hold out 10% of the data as CV set
	for i in range(n):
		X_train, X_cv, y_train, y_cv = cross_validation.train_test_split(
		      sample_X, sample_y, test_size=.10, random_state=i*SEED)
		# train with rand...
		random_search.fit(X_train, y_train)
		# train...
		#regressor = regressor.fit(X_train, y_train)
		# save model
		#store_pkl(regressor, name + ".pkl")
		# predict on train
		preds = random_search.predict(X_cv)
		# print 
		#print preds
		# create DataFrame
		#preds = DataFrame(preds, columns = ["prime_tot_ttc_preds"])
		#print preds
		#print y_cv
		# mape
		mape_r = mape(y_cv, preds)
		# print
		print "MAPE of (fold %d/%d) of %s is : %f" % (i+1 , n, name, mape_r)
		# time...
		print("RandomizedSearchCV took %.2f seconds for %d candidates"
		      " parameter settings." % ((time() - start), n_iter_search))
		report(random_search.grid_scores_)
	# predict on test
	predict_res = random_search.predict(sample_t)
	preds_on_test = DataFrame(list(zip(sample_id, predict_res)), columns = ["ID", "CODIS"])
	preds_on_test['ID'].astype(int)
	# save predictions
	store_csv(preds_on_test, name + ".csv")
	return predict_res




sample = load_csv("sample.csv")

print sample.dtypes

sample['id'].astype(int)
sample['ann_obt_permis'] = sample['annee_permis'] - sample['annee_naissance']
sample['duree_permis'] = 2016 - sample['annee_permis']

print(sample.dtypes)

mapper = DataFrameMapper([
	(["id"], None),
	(["crm", 
	"ann_obt_permis", 
	"duree_permis", 
	"var1",
	"var2",
	"var3",
	"var4",
	"var5",
	"var17",
	"var18",
	"var19",
	"var20",
	"var21",
	"var22",
	"var9",
	"var10",
	"var11",
	"var12",
	"var13",
	"kmage_annuel",
	"puis_fiscale",
	"anc_veh","var15"], 
	[ContinuousDomain(), StandardScaler()]),
	(["marque"], LabelEncoder()),
	(["energie_veh"], LabelEncoder()), 
        (["profession"], LabelEncoder()), 
        (["var6"], LabelEncoder()),
        (["var7"], LabelEncoder()),
        (["var8"], LabelEncoder()),
        (["var16"], LabelEncoder()),
	(["prime_tot_ttc"], None)
])


sample_mapper = mapper.fit_transform(sample)

print sample_mapper.shape
#print sample_mapper.columns.tolist()

store_pkl(mapper, "mapper.pkl")

sample_X = sample_mapper[0:300000, 1:31]
sample_y = sample_mapper[0:300000, 31]
sample_t = sample_mapper[300000:330000, 1:31]
sample_id = sample_mapper[300000:330000, 0]

print sample_X.shape
print sample_y.shape
print sample_t.shape


predict_res_1 = build_sample(DecisionTreeRegressor(random_state = 13, min_samples_leaf = 5), "DecisionTreeAuto")
#predict_res_2 = build_sample(ExtraTreesRegressor(random_state = 13, min_samples_leaf = 5), "ExtraTreesAuto")
#predict_res_3 = build_sample(GradientBoostingRegressor(random_state = 13, init = None), "GradientBoostingAuto")
#predict_res_4 = build_sample(RandomForestRegressor(random_state = 13, min_samples_leaf = 5), "RandomForestAuto")


d = {"id":sample_id, "DecisionTreeAuto":predict_res_1}#, "ExtraTreesAuto":predict_res_2, "GradientBoostingAuto":predict_res_3, "RandomForestAuto":predict_res_4, }
global_result = DataFrame(d)
#global_result = DataFrame(list(zip(sample_id, predict_res_1,predict_res_2, predict_res_3, predict_res_4)), columns = ["id", "DecisionTreeAuto", "ExtraTreesAuto", "GradientBoostingAuto", "RandomForestAuto"])
store_csv(global_result, "global_result.csv")

#print(auto_X.dtype, auto_y.dtype)
#build_sample(DecisionTreeRegressor(random_state = 13, min_samples_leaf = 5), "DecisionTreeAuto")
#build_sample(BaggingRegressor(DecisionTreeRegressor(random_state = 13, min_samples_leaf = 5), random_state = 13, n_estimators = 3, max_features = 0.5), "DecisionTreeEnsembleAuto")
#build_sample(ElasticNetCV(random_state = 13), "ElasticNetAuto")
#build_sample(LassoCV(random_state = 13), "LassoAuto")
#build_sample(LinearRegression(), "LinearRegressionAuto")
#build_sample(BaggingRegressor(LinearRegression(), random_state = 13, max_features = 0.5), "LinearRegressionEnsembleAuto")
#build_sample(RidgeCV(), "RidgeAuto")
#build_sample(XGBRegressor(objective = "reg:linear"), "XGBAuto")
