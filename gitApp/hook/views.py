from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from hook.helper import pretty_request
from checks import CheckFlow
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

    try:
        event_type = request.headers["X-Github-Event"]
        print(f"HOOK CALLED: {event_type}")
    except Exception as e:
        print(e)
        return HttpResponse("Not a X-Github-Event type request.")

    #TODO: HANDLE RE-REQUEST EVENTS for single runs and entire suits

    if "pull_request" in event_type:
        request_json = json.loads(request.body)
        action = request_json["action"]

        # TODO: Re-enable these triggers
        if action == "opened" \
                or action == "synchronize"\
                or action == "reopened":
            print('\n\n\nDEBUG: NOT RUNNING FOR ALL PULL REQUESTS\n\n\n')

        if action == "labeled":
            labels = request_json['pull_request']['labels']
            for l in labels:
                if l['name'] == 'test-performance':
                    print('\n\n\nLABEL-TRIGGER\n\n\n')
                    try:
                        check = CheckFlow()
                        check.receiveHook(request)
                    except Exception as e:
                        print(f"CheckFlow failed with {e}")

                    continue


    return HttpResponse(status=201)

