import json
import os
import sys
from dataclasses import dataclass

import requests
from decorator import append
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from slack import Slack

TODO = 'TODO'
IN_PROGRESS = 'IN_PROGRESS'
PUT_OFF = 'PUT_OFF'
ON_STAGE = 'ON_STAGE'
WAIT_FOR_STAGE = 'WAIT_FOR_STAGE'
ON_PROD = 'ON_PROD'
ON_PREPROD = 'ON_PREPROD'
DONE = 'DONE'


@dataclass
class JiraClient:
    project_url: str
    current_ticket = ''
    _auth: HTTPBasicAuth
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    _statusesMap = {}
    _assigneeMap = {}

    def __init__(self):
        self._auth = HTTPBasicAuth(
            os.environ.get('JIRA_EMAIL'),
            os.environ.get('JIRA_TOKEN')
        )

        self.project_url = os.environ.get('JIRA_PROJECT_URL')

    def get_url(self):
        return f'{self.project_url}/rest/api/3/issue/{self.current_ticket}'

    def create_comment(self, current_ticket: str, **kwargs):
        self.current_ticket = current_ticket

        if kwargs.get('commit'):
            commit = kwargs.get('commit')
            payload = json.dumps({
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "content": [
                                {
                                    "attrs": {
                                        "url": commit
                                    },
                                    "type": "inlineCard"
                                },
                                {
                                    "text": " ",
                                    "type": "text"
                                }
                            ],
                            "type": "paragraph"
                        }
                    ],

                }
            })

        if kwargs.get('comment'):
            comment = kwargs.get('comment')
            payload = json.dumps({
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "text": comment,
                                    "type": "text"
                                }
                            ]
                        }
                    ]
                }
            })
        return requests.request(
            'POST',
            self.get_url() + '/comment',
            data=payload,
            headers=self._headers,
            auth=self._auth
        )

    def get_comments(self, current_ticket):
        self.current_ticket = current_ticket
        print(self.get_url() + '/comment')
        return self.get_request(self.get_url() + '/comment')

    def get_status_by_alias(self, alias):
        if alias in self._statusesMap:
            return self._statusesMap[alias]
        else:
            raise Exception('Status ID for ALIAS ' + alias + ' not found')

    def set_status(self, current_ticket, status):
        self.current_ticket = current_ticket
        return self.post_request(
            self.get_url() + '/transitions',
            json.dumps({
                "transition": {"id": self.get_status_by_alias(status)}
            }))

    def set_assignee(self, current_ticket, assignee=None):
        self.current_ticket = current_ticket
        return self.put_request(
            self.get_url() + '/assignee',
            json.dumps({"accountId": assignee})
        )

    def load_transitions(self, current_ticket):
        self.current_ticket = current_ticket

        transitions_response = self.get_request(self.get_url() + '/transitions')
        if transitions_response.status_code == 200:
            transitions = transitions_response.json()['transitions']
            for transition in transitions:
                prepared_name = str(transition['name']).upper().replace(" ", "_")
                self._statusesMap[prepared_name] = transition['id']
        else:
            print(transitions_response.status_code)
        return self._statusesMap

    def load_assignee(self, current_ticket):
        self.current_ticket = current_ticket

        assignee_response = self.get_request(self.get_url() + '/assignee')
        if assignee_response.status_code == 200:
            assignees = assignee_response.json()['assignee']
            print(assignees)
            for assignee in assignees:
                prepared_name = str(assignee['name']).upper().replace(" ", "_")
                self._assigneeMap[prepared_name] = assignee['id']
        else:
            print(assignee_response.status_code)
        return self._assigneeMap

    def get_request(self, url):
        return requests.get(
            url,
            headers=self._headers,
            auth=self._auth
        )

    def post_request(self, url, payload: dict):
        return requests.request(
            'POST',
            url,
            data=payload,
            headers=self._headers,
            auth=self._auth
        )

    def put_request(self, url, payload: dict):
        return requests.request(
            'PUT',
            url,
            data=payload,
            headers=self._headers,
            auth=self._auth
        )


load_dotenv()

slack = Slack()

r = slack.push_release_message("release message")
print(r.status_code)
sys.exit("Debug exit")

jira = JiraClient()
# r = jira.create_comment('TEST-1', commit="https://www.geeksforgeeks.org/convert-json-to-dictionary-in-python/")
# r = jira.get_comments('TEST-1')
jira.load_transitions('TEST-1')
r = jira.set_status('TEST-1', 'DONE')
r = jira.set_assignee('TEST-1')
print(r.status_code)
print(r.text)


parsed = json.loads(r.text)
print(json.dumps(parsed, indent=4, sort_keys=True))
