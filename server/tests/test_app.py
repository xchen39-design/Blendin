import unittest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from server.main import app, matches, parse_events, SOURCES, club_matches

class BlendinTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_has_directory(self):
        self.assertGreater(self.client.get('/api/health').json()['clubs'], 100)

    def test_empty_and_excessive_requests_rejected(self):
        for body in [{'interests': []}, {'interests': ['  ']}, {'interests': ['music'], 'top_k': 100}, {'interests': ['x' * 61]}]:
            self.assertEqual(self.client.post('/api/recommend', json=body).status_code, 422)

    def test_local_matches_without_network(self):
        with patch('server.main.discover_events', new_callable=AsyncMock) as discover:
            response = self.client.post('/api/recommend', json={'interests': ['music'], 'top_k': 3})
            discover.assert_not_called()
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['items'])
        self.assertLessEqual(len(result['items']), 3)
        self.assertTrue(all(item['type'] == 'club' for item in result['items']))

    def test_short_ai_does_not_match_unrelated_words(self):
        self.assertFalse(matches('ai', 'sailing'))
        self.assertFalse(matches('art', 'martialarts'))
        self.assertTrue(matches('acm', 'acm'))
        self.assertTrue(club_matches(['coding']))

    def test_parser_excludes_navigation_and_unsafe_links(self):
        html = '<a href="/calendar">Music calendar</a><a href="javascript:alert(1)">Music</a><a href="https://evil.example/event/view/1">Music</a><a href="/event/view/wm/123">Music performance</a><a href="/event/view/wm/124">Football game</a>'
        items = parse_events(html, SOURCES[0][1], ['music'], 'W&M')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['url'], 'https://events.wm.edu/event/view/wm/123')

    def test_sports_does_not_match_growing(self):
        html = '<a href="/event/view/wm/1">Growing flood losses</a>'
        self.assertEqual(parse_events(html, SOURCES[0][1], ['sports'], 'W&M'), [])

    def test_provider_failure_retains_clubs(self):
        with patch('server.main.discover_events', new_callable=AsyncMock, return_value=([], ['Source unavailable'])):
            result = self.client.post('/api/recommend', json={'interests': ['music'], 'live_events': True}).json()
        self.assertTrue(result['items'])
        self.assertIn('Source unavailable', result['warnings'])

    def test_timeout_retains_clubs(self):
        with patch('server.main.discover_events', new_callable=AsyncMock, side_effect=TimeoutError):
            result = self.client.post('/api/recommend', json={'interests': ['music'], 'live_events': True}).json()
        self.assertTrue(result['items'])
        self.assertIn('timed out', result['warnings'][0])

    def test_unknown_interest_is_not_fabricated(self):
        result = self.client.post('/api/recommend', json={'interests': ['zznonexistentinterest']}).json()
        self.assertEqual(result['items'], [])
        self.assertEqual(len(result['calendars']), 2)

    def test_live_events_precede_clubs(self):
        event = {'type':'event','title':'Music concert','url':'https://events.wm.edu/event/view/wm/123','score':1,'reason':'listing','source':'W&M'}
        with patch('server.main.discover_events', new_callable=AsyncMock, return_value=([event], [])):
            result = self.client.post('/api/recommend', json={'interests':['music'], 'live_events':True}).json()
        self.assertEqual(result['items'][0]['type'], 'event')
        self.assertTrue(any(item['type'] == 'club' for item in result['items']))

if __name__ == '__main__':
    unittest.main()
