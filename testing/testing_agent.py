#!/usr/bin/python
# -*- coding: utf8 -*-

from datetime import datetime, timedelta
from base_test_case import BaseTestCase
from models import JournalTag, Goal, User
from flow import app as tst_app
from services.agent import ConversationAgent
from models import Habit, Task


class AgentTestCase(BaseTestCase):

    def setUp(self):
        self.set_application(tst_app)
        self.setup_testbed()
        self.init_datastore_stub()
        self.init_memcache_stub()
        self.init_taskqueue_stub()
        self.init_mail_stub()
        self.register_search_api_stub()
        self.init_app_basics()

        self.u = u = self.users[0]
        self.u.Update(name="George")
        self.u.put()
        h = Habit.Create(u)
        h.Update(name="Run")
        h.put()
        t = Task.Create(u, "Dont forget the milk")
        t.put()
        g = Goal.Create(u, date=datetime.today().date())
        g.Update(text=["Get it done", "Also get exercise"])
        g.put()

        self.ca = ConversationAgent(user=self.u)

    def test_agent_status_query(self):
        speech, data = self.ca.respond_to_action('input.status_request')
        self.assertEqual(speech, "Alright George. You've completed 0 tasks for today. You still need to do 'Dont forget the milk'.")

    def test_agent_goals(self):
        speech, data = self.ca.respond_to_action('input.goals_request')
        this_month = datetime.strftime(datetime.today(), "%B %Y")
        self.assertEqual(speech, "Goals for %s. 1: Get it done. 2: Also get exercise. " % this_month)

    def test_agent_habit_report(self):
        speech, data = self.ca.respond_to_action('input.habit_report', parameters={'habit': 'run'})
        self.assertTrue("'Run' is marked as complete" in speech, speech)

    def test_agent_habit_commitment(self):
        speech, data = self.ca.respond_to_action('input.habit_commit', parameters={'habit': 'run'})
        self.assertTrue("You've committed to 'Run' today" in speech, speech)

    def test_agent_no_user(self):
        self.ca.user = None
        speech, data = self.ca.respond_to_action('input.status_request')
        self.assertEqual("Uh oh, is your account linked?", speech)

    def test_parsing(self):
        volley = [
            # Goal requests
            ('what are my goals?', 'input.goals_request', None),
            ('remind me my goals', 'input.goals_request', None),
            ('monthly goals', 'input.goals_request', None),
            ('my goals this month', 'input.goals_request', None),

            # Habit reports
            ('mark run as complete', 'input.habit_report', {'habit': 'run'}),
            ('mark run as done', 'input.habit_report', {'habit': 'run'}),
            ('mark meditate as finished', 'input.habit_report', {'habit': 'meditate'}),
            ('i finished meditate', 'input.habit_report', {'habit': 'meditate'}),
            ('set run as complete', 'input.habit_report', {'habit': 'run'}),

            # Habit commitments
            ('i will run tonight', 'input.habit_commit', {'habit': 'run'}),
            ('commit to make dinner tonight', 'input.habit_commit', {'habit': 'make dinner'}),
            ('planning to run this evening', 'input.habit_commit', {'habit': 'run'}),
            ('im going to run later', 'input.habit_commit', {'habit': 'run'}),
        ]
        for v in volley:
            raw_message, expected_action, expected_params = v
            action, params = self.ca.parse_message(raw_message)
            self.assertEqual(expected_action, action, raw_message)
            self.assertEqual(expected_params, params, raw_message)

