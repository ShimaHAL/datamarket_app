from typing import List, Dict, Any
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import HttpRequest, HttpResponse, JsonResponse

from janome.analyzer import Analyzer
from janome.tokenfilter import POSKeepFilter, LowerCaseFilter, ExtractAttributeFilter

import requests

def index(request: HttpRequest)-> HttpResponse:
    return render(request, 'dmapp/index.html')


@require_POST
def search(request: HttpRequest)-> HttpResponse:
    token_filters = [
        POSKeepFilter(['名詞', "動詞", "形容詞", "形容動詞"]),
        LowerCaseFilter(),
        ExtractAttributeFilter('base_form')
    ]
    analyzer = Analyzer(token_filters=token_filters)

    dj:str=str(request.POST["dj"])
    dj_wakati:List[str]=list(analyzer.analyze(dj))

    req:str = str(request.POST["request"])
    req_wakati:List[str]=list(analyzer.analyze(req))

    sol:str=str(request.POST["solution"])
    sol_wakati:List[str]=list(analyzer.analyze(sol))

    url: str = "https://datajacket-store.org/sparql"
    dj_query_base: str =  \
        "select ?dj_ID ?DJ ?sol ?req where{\
        ?s rdfs:label ?sol;\
        <http://datajacket.org/solution/id> ?sol_ID;\
        <http://datajacket.org/solution/combine> ?dj_URI;\
        <http://datajacket.org/solution/satisfy> ?req_URI.\
        ?req_URI rdfs:label ?req;\
        <http://datajacket.org/requirement/id> ?req_ID.\
        ?dj_URI rdfs:label ?DJ;\
        <http://datajacket.org/datajacket/id> ?dj_ID."

    dj_query: str = ""
    if len(dj_wakati) > 0:
        dj_query += "FILTER ("
        dj_query += " || ".join(["regex(?DJ, \"" + w + "\")" for w in dj_wakati])
        dj_query += ")."

    req_query_base: str = \
        "{?s rdfs:label ?sol;\
        <http://datajacket.org/solution/id> ?sol_ID;\
        <http://datajacket.org/solution/combine> ?dj_URI.\
        ?dj_URI rdfs:label ?DJ;\
        <http://datajacket.org/datajacket/id> ?dj_ID."

    req_query: str = ""
    if len(req_wakati) > 0:
        req_query += "FILTER ("
        req_query += " || ".join(["regex(?req, \"" + w + "\")" for w in req_wakati])
        req_query += ")."

    
    params: str = "&format=application%2Fsparql-results%2Fhtml&timeout=0&debug=on&run=+Run+Query+"


    res = requests.get(url+query+params)



    context: Dict[str, Any]={"message": "search", "dj":dj_wakati, "sol": sol_wakati}
    print(dj_wakati, sol_wakati)
    return JsonResponse(context)


@require_POST
def feellucky(request: HttpRequest)-> HttpResponse:
    return JsonResponse({"message": "feel lucky"})
