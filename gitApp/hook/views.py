from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helper import pretty_request
from .checkFlow import CheckFlow

# Create your views here.
@csrf_exempt
def base(request):

    pretty_request(request)

    response_text = "Hey There"
    return HttpResponse(response_text)

@csrf_exempt
def receiveHook(request):

    pretty_request(request)

    event_type = request.headers["X-Github-Event"]
    print(f"HOOK CALLED: {event_type}")

    if "pull_request" in event_type:
        print ("do pull stuff")
        check = CheckFlow()
        check.receiveHook(request)

    return HttpResponse(status=201)

