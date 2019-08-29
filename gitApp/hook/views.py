from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from hook.helper import pretty_request
from hook.CheckFlow import CheckFlow
import json

# Create your views here.
@csrf_exempt
def base(request):

    pretty_request(request)

    response_text = "Hey There"
    return HttpResponse(response_text)

@csrf_exempt
def receiveHook(request):
    """ Deal with incoming web hook """

    # On push associated with pull request will receive:
    #   1. Push Event
    #   2. Check_Suite Event
    #   3. Pull Request Event

    pretty_request(request)

    event_type = request.headers["X-Github-Event"]
    print(f"HOOK CALLED: {event_type}")

    #TODO: HANDLE RE-REQUEST EVENTS for single runs and entire suits

    if "pull_request" in event_type:
        action = json.loads(request.body)["action"]
        if action == "opened" \
                or action == "synchronize"\
                or action == "reopened":
            print ("do pull stuff")
            check = CheckFlow()
            check.receiveHook(request)

    return HttpResponse(status=201)

