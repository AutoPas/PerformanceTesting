from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests

def pretty_request(request):

    for k, v in request.headers.items():
        print(k,v)

    jsonBody = json.loads(request.body.decode('utf-8'))
    print(json.dumps(jsonBody, indent=4, sort_keys=True))

# Create your views here.
@csrf_exempt
def base(request):

    pretty_request(request)

    response_text = "Hey There"
    return HttpResponse(response_text)

@csrf_exempt
def receiveHook(request):

    pretty_request(request)

    print("hook called")
    return HttpResponse("200")