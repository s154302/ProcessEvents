import json
import time

from urllib import request, parse, error
owner = "s154302"
repo = "ProcessEvents"
Etag = ""
event_set = set()
while(True):
    try:
        # Github Events API is documented at https://developer.github.com/v3/activity/events/
        print("polling Github repository {0} owned by {1} for events".format(repo, owner))
        url = 'https://api.github.com/repos/{0}/{1}/events'.format(owner, repo)
        requestGit = request.Request(url)

        # The Etag is used to identify whether there are any new events since previous poll
        if Etag != "":
            print("Setting Etag to {}".format(Etag))
            requestGit.add_header('If-None-Match', Etag)

        response = request.urlopen(requestGit)
        datastore = json.loads(response.read().decode('utf-8'))
        
        # The poll interval header specifies how often polling the API is allowed
        poll_interval = int(response.info()["X-poll-interval"])
        Etag = response.info()["Etag"]

    # A 304 is returned if there are no new events since previous poll
    except error.HTTPError as e:
        poll_interval = int(response.info()["X-poll-interval"])
        if e.code == 304 :
            print("No new events. Waiting {} seconds before polling again".format(poll_interval))
            time.sleep(poll_interval)
            continue

    start = time.time()

    for event in datastore:

        # Check if the event has already been seen
        if event["id"] in event_set:
            continue
        else:
            event_set.add(event["id"])

        print(event["type"])

        # Define stream url. Since response for Issues is different, different stream must be used
        # /Github/Issues for issue events and /Github/Events for regular events
        streamUrl = 'http://localhost:8080/GithubEvents/Github/Issues' if "Issue" in event["type"] else 'http://localhost:8080/GithubEvents/Github/Events'
        print("Posting event to {} stream".format(streamUrl))

        requestStream = request.Request(streamUrl)

        json_data = json.dumps(event)
        data_bytes = json_data.encode('utf-8')

        requestStream.add_header('Content-Type', 'application/json')

        resp = request.urlopen(requestStream, data_bytes)

    end = time.time()
    print(end - start)
    if end - start < poll_interval:
        remaining_time = poll_interval - int(end - start)
        print("Waiting {} seconds before polling again".format(remaining_time))
        time.sleep(remaining_time)
