#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Alberto Martín <alberto.martin@bitergia.com>
#

import unittest
import sys

import httpretty

from perceval.backends.jira import JiraClient
from perceval.utils import str_to_datetime

if not '..' in sys.path:
    sys.path.insert(0, '..')

JIRA_SERVER_URL = 'http://example.com'
JIRA_SEARCH_URL = JIRA_SERVER_URL + '/rest/api/2/search'


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


class TestJiraClient(unittest.TestCase):
    def test___init__(self):
        client = JiraClient(url='http://example.com', project='perceval',
                            user='user', password='password',
                            verify=False, cert=None, max_issues=100)
        self.assertEqual(client.url, 'http://example.com')
        self.assertEqual(client.project, 'perceval')
        self.assertEqual(client.user, 'user')
        self.assertEqual(client.password, 'password')
        self.assertEqual(client.verify, False)
        self.assertEqual(client.cert, None)
        self.assertEqual(client.max_issues, 100)

    @httpretty.activate
    def test_get_issues(self):

        from_date = str_to_datetime('2015-01-01')

        requests = []

        bodies_json = [read_file('data/jira/jira_issues_page_1.json'),
                       read_file('data/jira/jira_issues_page_2.json')]

        def request_callback(method, uri, headers):
            body = bodies_json.pop(0)
            requests.append(httpretty.last_request())
            return (200, headers, body)

        httpretty.register_uri(httpretty.GET,
                               JIRA_SEARCH_URL,
                               responses=[httpretty.Response(body=request_callback) \
                                          for _ in range(2)])

        client = JiraClient(url='http://example.com', project='perceval',
                            user='user', password='password',
                            verify=False, cert=None, max_issues=2)

        pages = [page for page in client.get_issues(from_date)]

        expected_req_0 = {
                        'expand': ['renderedFields,transitions,operations,changelog'],
                        'jql': [' project = perceval AND  updated > "2015-01-01 00:00"'],
                        'maxResults': ['2'],
                        'startAt': ['0']
                        }
        expected_req_1 = {
                        'expand': ['renderedFields,transitions,operations,changelog'],
                        'jql': [' project = perceval AND  updated > "2015-01-01 00:00"'],
                        'maxResults': ['2'],
                        'startAt': ['2']
                        }

        self.assertEqual(len(pages), 2)

        self.assertEqual(requests[0].method, 'GET')
        self.assertRegex(requests[0].path, '/rest/api/2/search')
        self.assertDictEqual(requests[0].querystring, expected_req_0)

        self.assertEqual(requests[1].method, 'GET')
        self.assertRegex(requests[1].path, '/rest/api/2/search')
        self.assertDictEqual(requests[1].querystring, expected_req_1)

if __name__ == '__main__':
    unittest.main(warnings='ignore')
