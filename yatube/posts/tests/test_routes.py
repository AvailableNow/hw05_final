from django.test import TestCase
from django.urls import reverse


from ..urls import app_name

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
    ('follow_index', '/follow/'),
    ('profile_follow', f'/profile/{USERNAME}/follow/', USERNAME),
    ('profile_unfollow', f'/profile/{USERNAME}/unfollow/', USERNAME),
    ('add_comment', f'/posts/{POST_ID}/comment/', POST_ID)
}


class RoutesTest(TestCase):
    def test_routes(self):
        for routes, address, *keys, in TEST_URLS:
            with self.subTest(routes=routes):
                self.assertEqual(reverse(
                    f'{app_name}:{routes}', args=keys), address)
