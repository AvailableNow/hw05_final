import shutil
import tempfile

from django.core.cache import cache
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User, Follow
POSTS_COUNT = 13
POSTS_SECOND_PAGE = 4
NIK_1 = 'test_user'
NIK_2 = 'test_author'
NIK_3 = 'testauthor_3'
NIK_4 = 'testauthor_4'
SLUG_1 = 'test_slug_1'
SLUG_2 = 'test_slug_2'
SLUG_3 = 'test_slug_3'

POST_TEST = 'ш' * 50
SMALL_GIF = SimpleUploadedFile(
    name='small.gif',
    content=(
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    ),
    content_type='image/gif'
)
MAIN_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
GROUP_URL = reverse(
    'posts:group_list',
    args=[SLUG_1]
)
GROUP_URL_2 = reverse(
    'posts:group_list',
    args=[SLUG_2]
)
ANOTHER_GROUP_URL = reverse(
    'posts:group_list',
    args=[SLUG_3]
)
PROFILE_URL = reverse(
    'posts:profile',
    args=[NIK_2]
)
MAIN_PAGE_PAGINATOR_SECOND = MAIN_URL + '?page=2'
GROUP_URL_2_SECOND = f'{GROUP_URL_2}?page=2'
PROFILE_PAGINATOR_SECOND = f'{PROFILE_URL}?page=2'
FOLLOW_URL_SECOND = f'{FOLLOW_URL}?page=2'

FOLLOW = reverse(
    'posts:profile_follow',
    args=[NIK_1]
)
UNFOLLOW = reverse(
    'posts:profile_unfollow',
    args=[NIK_1]
)
FOLLOW_USER_URL = reverse(
    'posts:profile_follow',
    args=[NIK_2]
)
UNFOLLOW_USER_URL = reverse(
    'posts:profile_unfollow',
    args=[NIK_2]
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# @override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug=SLUG_1,
            description='Тестовое описание 1',
        )

        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG_2,
            description='Тестовое описание',
        )

        cls.group_3 = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG_3,
            description='Тестовое описание',
        )
        cls.user_test = User.objects.create_user(username=NIK_1)
        cls.author_test = User.objects.create(username=NIK_2)
        cls.follower_user = User.objects.create_user(username=NIK_3)
        cls.non_follower_user = User.objects.create_user(username=NIK_4)
        cls.post = Post.objects.create(
            text=POST_TEST,
            group=cls.group,
            author=cls.author_test,
            image=SMALL_GIF
        )
        # библиотека урлов
        cls.POST_PAGE_URL = reverse(
            'posts:post_detail', args=[cls.post.id]
        )
        # первый клиент автор поста
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized_author = Client()
        cls.follower_client = Client()
        cls.non_follower_client = Client()

        cls.authorized.force_login(cls.user_test)
        cls.authorized_author.force_login(cls.author_test)
        cls.follower_client.force_login(cls.follower_user)
        cls.non_follower_client.force_login(cls.non_follower_user)

    # Удаляем временную папку
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_group_profile_show_correct_context(self):
        """Шаблоны index,group,profile сформированы с правильным контекстом."""
        Follow.objects.create(
            author=self.author_test,
            user=self.user_test,
        )
        urls = {
            PROFILE_URL: 'page_obj',
            FOLLOW_URL: 'page_obj',
            MAIN_URL: 'page_obj',
            GROUP_URL: 'page_obj',
            self.POST_PAGE_URL: 'post',
        }
        for url, context_name in urls.items():
            with self.subTest(url=url):
                response = self.authorized.get(url)
                if context_name == 'page_obj':
                    self.assertEqual(len(response.context.get('page_obj')), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
            self.assertEqual(self.post.text, post.text)
            self.assertEqual(self.post.author, post.author)
            self.assertEqual(self.post.group, post.group)
            self.assertEqual(self.post, post)
            self.assertEqual(self.post.image, post.image)

    def test_profile_has_correct_context(self):
        """Автор в контексте Профиля"""
        response = self.authorized_author.get(PROFILE_URL)
        self.assertEqual(
            response.context['author'], self.author_test
        )

    def test_group_list_has_correct_context(self):
        """Группа в контексте Групп-ленты без искажения атрибутов"""
        response = self.authorized.get(GROUP_URL)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.pk, self.group.pk)

    def test_post_did_not_appear_on_another_group_feed(self):
        """Пост не попал на чужую Групп-ленту"""
        response = self.authorized_author.get(ANOTHER_GROUP_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_paginator(self):
        COUNT = settings.MAX_POSTS + POSTS_SECOND_PAGE
        Follow.objects.create(
            author=self.author_test,
            user=self.user_test,
        )
        Post.objects.bulk_create(
            Post(
                text=f"Тестовый текст{i}",
                author=self.author_test,
                group=self.group_2
            )
            for i in range(COUNT - Post.objects.all().count())
        )
        urls = {
            MAIN_URL: settings.MAX_POSTS,
            MAIN_PAGE_PAGINATOR_SECOND: POSTS_SECOND_PAGE,
            GROUP_URL_2: settings.MAX_POSTS,
            PROFILE_URL: settings.MAX_POSTS,
            PROFILE_PAGINATOR_SECOND: POSTS_SECOND_PAGE,
            FOLLOW_URL: settings.MAX_POSTS,
            FOLLOW_URL_SECOND: POSTS_SECOND_PAGE,
        }
        for url, number in urls.items():
            with self.subTest(url=url, number=number):
                self.assertEqual(
                    len(self.authorized.get(url).context['page_obj']), number
                )

    def test_index_cache(self):
        """Проверка кэша на странице на главной странице."""
        response_1 = self.authorized.get(MAIN_URL)
        Post.objects.all().delete()
        response_2 = self.authorized.get(MAIN_URL)
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized.get(MAIN_URL)
        self.assertNotEqual(response_2.content, response_3.content)

    def test_following(self):
        """Проверка подписки на автора."""
        followes_count = Follow.objects.count()
        self.follower_client.get(FOLLOW)
        self.assertEqual(followes_count + 1, Follow.objects.count())
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower_user,
                author=self.user_test).exists()
        )

    def test_unfollowing(self):
        """Проверка отписки на автора."""
        Follow.objects.create(
            user=self.follower_user,
            author=self.user_test
        )
        followes_count = Follow.objects.count()
        self.follower_client.get(UNFOLLOW)
        self.assertEqual(followes_count - 1, Follow.objects.count())
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower_user,
                author=self.user_test).exists()
        )
