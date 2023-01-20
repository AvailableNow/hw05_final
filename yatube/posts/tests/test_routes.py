from django.test import TestCase
from django.urls import reverse

USERNAME = 'test_user'
SLUG = 'test_group'
POST_ID = 1
TEST_URLS = {
    ('index', '/'),
    ('post_create', '/create/'),
    ('group_list', f'/group/{SLUG}/', SLUG),
    ('profile', f'/profile/{USERNAME}/', USERNAME),
    ('post_detail',
     f'/posts/{POST_ID}/', POST_ID),
    ('post_edit',
     f'/posts/{POST_ID}/edit/', POST_ID),
}


class RoutesTest(TestCase):
    def test_routes(self):
        for routes, address, *keys, in TEST_URLS:
            with self.subTest(routes=routes):
                self.assertEqual(reverse(
                    f'posts:{routes}', args=keys), address)
