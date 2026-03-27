import json

import requests
from django.conf import settings
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
)

GOOGLE_URL_BASE = "https://maps.googleapis.com/maps/api/place/"


def google_autocomplete(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    query = request.GET.get("query", "").strip()
    if not query:
        return HttpResponseBadRequest()
    callback = request.GET.get("callback", None)

    if not hasattr(settings, "GOOGLE_API_KEY"):
        return HttpResponseNotFound("No API key configured")
    language = request.GET.get("language", "en")
    args = {"key": settings.GOOGLE_API_KEY, "language": language, "sensor": "true"}
    args["input"] = query
    args["types"] = "geocode"
    if "country" in request.GET:
        args["components"] = "country:%s" % (request.GET["country"])

    r = requests.get(GOOGLE_URL_BASE + "autocomplete/json", params=args)
    if r.status_code != 200:
        return HttpResponseBadRequest()
    ret = r.json()
    s = json.dumps(ret)
    if callback:
        s = f"{callback} && {callback}({s});"
    return HttpResponse(s, content_type="application/json")


def google_details(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    ref = request.GET.get("reference", "").strip()
    if not ref:
        return HttpResponseBadRequest()
    callback = request.GET.get("callback", None)

    if not hasattr(settings, "GOOGLE_API_KEY"):
        return HttpResponseNotFound("No API key configured")
    language = request.GET.get("language", "en")
    args = {"key": settings.GOOGLE_API_KEY, "language": language, "sensor": "true"}
    args["reference"] = ref

    r = requests.get(GOOGLE_URL_BASE + "details/json", params=args)
    if r.status_code != 200:
        return HttpResponseBadRequest()
    ret = r.json()
    s = json.dumps(ret)
    if callback:
        s = f"{callback} && {callback}({s});"
    return HttpResponse(s, content_type="application/json")
