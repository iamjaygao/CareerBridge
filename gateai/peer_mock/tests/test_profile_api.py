"""
Onboarding and profile: GET/PUT me/profile/, GET meta/ (design doc §2.2).

The first PUT creates the profile and needs the current terms, an 18+
confirmation and (for the first cohort) a valid invite code.
"""

from datetime import timedelta

from django.test import TestCase, override_settings

from peer_mock.constants import TERMS_VERSION
from peer_mock.models import InviteCode, PeerEvent, PeerProfile, PreRegistration

from .helpers import NOW, client_for, frozen, make_invite, make_user, onboard, onboarding_body, power_peer_mock

URL = '/api/v1/peer-mock/me/profile/'


class PeerMockGateTest(TestCase):
    """Every PR1 endpoint: sign-in, verified email, bus and flag."""

    PATHS = ['/api/v1/peer-mock/meta/', URL, '/api/v1/peer-mock/rounds/current/']

    def setUp(self):
        power_peer_mock()
        self.user = make_user('alex')
        onboard(self.user)

    def test_anonymous_gets_401(self):
        for path in self.PATHS:
            with self.subTest(path=path):
                self.assertEqual(client_for(None).get(path).status_code, 401)

    def test_unverified_email_gets_403(self):
        unverified = make_user('unverified', verified=False)
        for path in self.PATHS:
            with self.subTest(path=path):
                response = client_for(unverified).get(path)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['code'], 'email_not_verified')

    def test_bus_off_or_flag_off_is_404(self):
        for bus, flag in (('OFF', 'ON'), ('ON', 'OFF')):
            power_peer_mock(bus=bus, flag=flag)
            for path in self.PATHS:
                with self.subTest(bus=bus, flag=flag, path=path):
                    self.assertEqual(client_for(self.user).get(path).status_code, 404)

    def test_round_endpoints_require_onboarding(self):
        newcomer = make_user('newcomer')
        response = client_for(newcomer).get('/api/v1/peer-mock/rounds/current/')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['code'], 'onboarding_required')

    def test_meta(self):
        body = client_for(self.user).get('/api/v1/peer-mock/meta/').json()
        self.assertEqual(body['interview_types'], ['coding', 'behavioral', 'system_design'])
        self.assertEqual(body['directions']['behavioral'], [])
        self.assertEqual(body['terms_version'], TERMS_VERSION)
        self.assertTrue(body['invite_required'])


class OnboardingTest(TestCase):

    def setUp(self):
        power_peer_mock()
        self.user = make_user('alex')
        self.client = client_for(self.user)
        self.invite, self.code = make_invite(max_uses=2)

    def put(self, **overrides):
        body = onboarding_body(invite_code=self.code)
        body.update(overrides)
        with frozen():
            return self.client.put(URL, body, format='json')

    def assert_rejected(self, response, code):
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(response.json()['code'], code)
        self.assertFalse(PeerProfile.objects.filter(user=self.user).exists())
        self.assertEqual(InviteCode.objects.get(pk=self.invite.pk).uses, 0)

    def test_get_before_onboarding_is_404_with_prefill(self):
        PreRegistration.objects.create(email='ALEX@example.com', display_name='Alex P', timezone='Europe/London',
                                       interview_type='coding', direction='backend')
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['code'], 'no_profile')
        self.assertEqual(response.json()['prefill'], {'display_name': 'Alex P', 'timezone': 'Europe/London',
                                                      'default_interview_type': 'coding',
                                                      'default_direction': 'backend'})

    def test_onboarding_creates_the_profile_and_uses_one_invite_slot(self):
        PreRegistration.objects.create(email='alex@example.com')
        response = self.put(invite_code=self.code.lower().replace('-', ' '))  # normalised
        self.assertEqual(response.status_code, 201, response.content)
        profile = PeerProfile.objects.get(user=self.user)
        self.assertEqual((profile.terms_version, profile.terms_accepted_at, profile.adult_confirmed_at),
                         (TERMS_VERSION, NOW, NOW))
        self.assertEqual(profile.invite_code, self.invite)
        self.assertEqual(InviteCode.objects.get(pk=self.invite.pk).uses, 1)
        self.assertEqual(PreRegistration.objects.get().claimed_by, self.user)
        self.assertEqual(response.json()['display_name'], 'Alex')

    def test_onboarding_events_carry_the_new_actor_ref(self):
        self.put()
        profile = PeerProfile.objects.get(user=self.user)
        events = PeerEvent.objects.filter(user=self.user)
        self.assertEqual(set(events.values_list('event_type', flat=True)), {'signup', 'onboarded'})
        self.assertEqual(set(events.values_list('actor_ref', flat=True)), {profile.actor_ref})
        self.assertEqual(events.get(event_type='onboarded').metadata, {'invite_label': 'cohort-1'})

    def test_terms_must_be_accepted(self):
        self.assert_rejected(self.put(accept_terms_version=''), 'terms_not_accepted')
        self.assert_rejected(self.put(accept_terms_version='2020-01-v0'), 'terms_not_accepted')

    def test_adult_confirmation_is_required(self):
        self.assert_rejected(self.put(confirm_adult=False), 'adult_confirmation_required')
        body = onboarding_body(invite_code=self.code)
        del body['confirm_adult']
        with frozen():
            self.assert_rejected(self.client.put(URL, body, format='json'), 'adult_confirmation_required')

    def test_invalid_invite_codes_are_rejected(self):
        self.assert_rejected(self.put(invite_code=''), 'invalid_invite_code')
        self.assert_rejected(self.put(invite_code='AAAA-BBBB-CCCC'), 'invalid_invite_code')
        expired, expired_code = make_invite('old', expires_at=NOW - timedelta(seconds=1))
        self.assert_rejected(self.put(invite_code=expired_code), 'invalid_invite_code')
        disabled, disabled_code = make_invite('off')
        InviteCode.objects.filter(pk=disabled.pk).update(active=False)
        self.assert_rejected(self.put(invite_code=disabled_code), 'invalid_invite_code')
        full, full_code = make_invite('full', max_uses=1)
        InviteCode.objects.filter(pk=full.pk).update(uses=1)
        self.assert_rejected(self.put(invite_code=full_code), 'invalid_invite_code')

    @override_settings(PEER_MOCK_INVITE_REQUIRED=False)
    def test_open_signup_needs_no_code(self):
        self.assertEqual(self.put(invite_code='').status_code, 201)

    def test_invalid_fields(self):
        for field, value in (('timezone', 'Mars/Olympus'), ('display_name', ''), ('display_name', 'x' * 41),
                             ('display_name', 'bad\u0000name'), ('default_interview_type', 'quant')):
            with self.subTest(field=field, value=value):
                response = self.put(**{field: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())
        response = self.put(default_interview_type='behavioral', default_direction='backend')
        self.assertEqual(response.status_code, 400)
        self.assertIn('direction', response.json())

    def test_later_updates_need_no_code_and_use_no_slot(self):
        self.assertEqual(self.put().status_code, 201)
        response = self.put(invite_code='', display_name='Alex R', timezone='Europe/London',
                            accept_terms_version='', confirm_adult=False)
        self.assertEqual(response.status_code, 200, response.content)
        profile = PeerProfile.objects.get(user=self.user)
        self.assertEqual((profile.display_name, profile.timezone), ('Alex R', 'Europe/London'))
        self.assertEqual(InviteCode.objects.get(pk=self.invite.pk).uses, 1)
        self.assertEqual(PeerEvent.objects.filter(event_type='onboarded').count(), 1)
