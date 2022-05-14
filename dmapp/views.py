from typing import List, Dict, Any
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


@require_POST
def search(request: HttpRequest) -> HttpResponse:

    search: str = str(request.POST["search"])

    if not search:
        return redirect(reverse("index"))

    else:
        token_filters = [
            POSKeepFilter(["名詞", "動詞", "形容詞"]),
            LowerCaseFilter(),
            ExtractAttributeFilter("base_form"),
        ]
        analyzer = Analyzer(token_filters=token_filters)

        wakati = list(analyzer.analyze(search))
        url: str = "https://datajacket-store.org/sparql"
        query: str = "select ?dj_ID ?DJ ?sol ?req where{\
            {?s rdfs:label ?sol;\
            <http://datajacket.org/solution/id> ?sol_ID;\
            <http://datajacket.org/solution/combine> ?dj_URI;\
            <http://datajacket.org/solution/satisfy> ?req_URI.\
            ?req_URI rdfs:label ?req;\
            <http://datajacket.org/requirement/id> ?req_ID.\
            ?dj_URI rdfs:label ?DJ;\
            <http://datajacket.org/datajacket/id> ?dj_ID."

        query += (
            "FILTER ("
            + " || ".join(['regex(?req, "' + w + '")' for w in wakati])
            + ")"
        )
        query += "} UNION {"
        query += (
            "FILTER ("
            + " || ".join(['regex(?sol, "' + w + '")' for w in wakati])
            + ")"
        )
        query += "} UNION {"
        query += "?s rdfs:label ?DJ; <http://datajacket.org/datajacket/id> ?dj_ID."
        query += (
            "FILTER ("
            + " || ".join(['regex(?DJ, "' + w + '")' for w in wakati])
            + ")"
        )
        query += "}}"
        query = "?query=" + urllib.parse.quote(query)

        params: str = "&format=application%2Fsparql-results%2Bjson&timeout=0&debug=on&run=+Run+Query+"
        print(url + query + params)
        res = requests.get(url + query + params)
        print(wakati)
        context: Dict[str, Any] = {"message": "search", "wakati": wakati}
        return JsonResponse(context)


@require_POST
def feellucky(request: HttpRequest) -> HttpResponse:
    return JsonResponse({"message": "feel lucky"})
