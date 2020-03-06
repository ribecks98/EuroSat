from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import CategoricalNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import scale
import sys
sys.path.append("../Classes")
sys.path.append("../DataProcessing")
sys.path.append("../")
from dataManip import *
from fileio import *
from Table import Table
import timeit
import matplotlib.pyplot as plt
import clfHelpers as helpers
import json
import Voters

def validateMethod(method):
    if not method in ['knn','bayes','forest','svm']:
        print("Invalid learning method")
        sys.exit()

def setupClf(method,param):
    if method == 'knn':
        return KNeighborsClassifier(n_neighbors=param)
    elif method == 'bayes':
        return CategoricalNB(alpha=param)
    elif method == 'forest':
        return RandomForestClassifier(\
            n_estimators=param[0],\
            max_depth=param[1],\
            min_samples_leaf=param[2],\
            ccp_alpha=param[3]\
        )
    elif method == 'svm':
        return SVC(C=param)

def setupParam(method,string):
    if method in ['bayes','svm']:
        return float(string)
    elif method == 'knn':
        return int(string)
    else:
        start = string.split(',')
        for i in range(3):
            start[i] = int(start[i])
        start[3] = float(start[3])
        print(start)
        return tuple(start)

def main(methods,params):
    start = timeit.default_timer()
    nerf = True
    if method in ["knn","svm"]:
        nerf = False
    with open("selectHeaders.json",'r') as f:
        select = json.load(f)
    select.append('satisfied')
    data = readCsv(\
        '../Data/Training/train_numeric.csv',\
        nerf=nerf\
    )
    data = selectCols(data,select)
    print("Reading time: ", timeit.default_timer()-start)

    headers = data[0]
    data = data[1:]
    
    start = timeit.default_timer()
    out = splitSamples(data)
    trainData = out[0]
    testData = out[1]
    
    out = separateCol(trainData,-1)
    trainData = out[0]
    trainData = deleteNCols(trainData,1)
    trainClasses = firstColVector(out[1])
    
    out = separateCol(testData,-1)
    testData = out[0]
    testIds = [testData[i][0] for i in range(len(testData))]
    testData = deleteNCols(testData,1)
    testClasses = firstColVector(out[1])
    print("Separation time: ", timeit.default_timer()-start)

    if method in ["knn","svm"]:
        trainData = scale(trainData)
        testData = scale(testData)
    
    arrs = []
    for i in range(len(methods)):
        table = Table()
        arr = [["ids","Predicted"]]
        start = timeit.default_timer()
        clf = setupClf(methods[i],params[i])
        clf.fit(trainData,trainClasses)
        print("Training time",methods[i],": ",timeit.default_timer()-start)

        start = timeit.default_timer()
        helpers.createTableWithArr(table,arr,clf,testData,testClasses,testIds)
        arrs.append(arr)

        print(str(table))
        print("Predicting time",methods[i],": ",timeit.default_timer()-start)

    voters = Voters.Voters()
    table = Table()
    for arr in arrs:
        voters.addVoter(arr)
    for i in range(len(testIds)):
        table.addObs(testClasses[i],voters.vote(testIds[i]))
    print(str(table))
    writeFile("../../Output/ensemble/"+methods[0]+"_"+str(params[0]),str(table))
    
if __name__ == "__main__":
    length = len(sys.argv)
    if length < 3:
        sys.exit()
    methods = []
    params = []
    for i in range(int(length/2)):
        method = sys.argv[2*i+1]
        validateMethod(method)
        param = setupParam(method,sys.argv[2*i+2])
        methods.append(method)
        params.append(param)
    main(methods,params)
