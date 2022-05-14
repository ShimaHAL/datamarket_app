from multiprocessing import Value
from typing import List, Dict, Any, Optional
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpRequest, HttpResponse, JsonResponse

from janome.analyzer import Analyzer
from janome.tokenfilter import POSKeepFilter, LowerCaseFilter, ExtractAttributeFilter

import requests
import urllib


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "dmapp/index.html")


def search(request: HttpRequest) -> HttpResponse:

    context: Dict[str, bool | str] = {}
    search_word: str = request.GET.get("search", "")

    if not search_word:
        context["status"] = False
        return JsonResponse(context)

    token_filters = [
        POSKeepFilter(["名詞", "動詞", "形容詞"]),
        LowerCaseFilter(),
        ExtractAttributeFilter("base_form"),
    ]
    analyzer = Analyzer(token_filters=token_filters)

    wakati = list(analyzer.analyze(search_word))
    url: str = "https://datajacket-store.org/sparql"

    query: str = ""
    mode: str = request.GET.get("mode", "dj")
    if mode == "DJ":
        query += "select ?id ?DJ where{\
            ?s <http://datajacket.org/datajacket/id> ?id;\
            rdfs:label ?DJ."

        query += (
            "FILTER (" + " || ".join(['regex(?DJ, "' + w + '")' for w in wakati]) + ")"
        )
        query += "}"
    elif mode == "req":
        query += "select ?id ?req where{\
            ?s <http://datajacket.org/solution/id> ?id;\
            rdfs:label ?req."
        query += (
            "FILTER (" + " || ".join(['regex(?req, "' + w + '")' for w in wakati]) + ")"
        )
        query += "}"

    else:  # mode=="sol"
        query += "select ?id ?sol where{\
            ?s <http://datajacket.org/requirement/id> ?id;\
            rdfs:label ?sol."
        query += (
            "FILTER (" + " || ".join(['regex(?sol, "' + w + '")' for w in wakati]) + ")"
        )
        query += "}"
    query = "?query=" + urllib.parse.quote(query)
    params: str = (
        "&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on&run=+Run+Query+"
    )
    res = requests.get(url + query + params)
    jsonList: List = res.json()["results"]["bindings"]
    context["status"] = True

    html: str = ""
    for data in jsonList:
        value: str = data[mode]["value"]
        html += "<tr>"
        html += f"<td data-value='{value}' onclick='searchAgain(this);'>{value}</td>"
        html += "</tr>"
    context["html"] = html
    return JsonResponse(context)
