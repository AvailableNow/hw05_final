import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

POSTS_SECOND_PAGE = 3
MAIN_URL = reverse('posts:index')
MAIN_PAGE_PAGINATOR_SECOND = MAIN_URL + '?page=2'
SLUG_1 = 'testslug_1'
NIK_1 = 'testauthor_1'
SLUG_2 = 'test_slug_2'
GROUP_URL = reverse(
    'posts:group_list',
    args=[SLUG_1]
)
GROUP_LIST_PAGINATOR_SECOND = f'{GROUP_URL}?page=2'
PROFILE_URL = reverse(
    'posts:profile',
    args=[NIK_1]
)
PROFILE_PAGINATOR_SECOND = f'{PROFILE_URL}?page=2'
ANOTHER_GROUP_URL = reverse(
    'posts:group_list',
    args=[SLUG_2]
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POST_TEST = 'ш' * 50


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
            title='Тестовая группа 2',
            slug=SLUG_2,
            description='Тестовое описание 1',
        )

        cls.user = User.objects.create_user(username=NIK_1)
        cls.post = Post.objects.create(
            text=POST_TEST,
            group=cls.group,
            author=cls.user
        )
        # библиотека урлов
        cls.POST_PAGE_URL = reverse(
            'posts:post_detail', args=[cls.post.id]
        )

    # Удаляем временную папку
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # первый клиент автор поста
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_group_profile_show_correct_context(self):
        """Шаблоны index,group,profile сформированы с правильным контекстом."""
        urls = {
            MAIN_URL: 'page_obj',
            GROUP_URL: 'page_obj',
            PROFILE_URL: 'page_obj',
            self.POST_PAGE_URL: 'post',
        }
        for url, context_name in urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                if context_name == 'page_obj':
                    self.assertEqual(len(response.context.get('page_obj')), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
            self.assertEqual(self.post.text, post.text)
            self.assertEqual(self.post.author, post.author)
            self.assertEqual(self.post.group, post.group)
            self.assertEqual(self.post, post)

    def test_profile_has_correct_context(self):
        '''Автор в контексте Профиля'''
        response = self.authorized_client.get(PROFILE_URL)
        self.assertEqual(
            response.context['author'], self.user
        )

    def test_group_list_has_correct_context(self):
        '''Группа в контексте Групп-ленты без искажения атрибутов'''
        response = self.authorized_client.get(GROUP_URL)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.pk, self.group.pk)

    def test_post_did_not_appear_on_another_group_feed(self):
        '''Пост не попал на чужую Групп-ленту'''
        response = self.authorized_client.get(ANOTHER_GROUP_URL)
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=NIK_1)
        cls.group_3 = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG_1,
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create(
            Post(
                text=f"Тестовый текст{i}",
                author=cls.user,
                group=cls.group_3
            )
            for i in range(settings.MAX_POSTS + POSTS_SECOND_PAGE)
        )
        cls.guest = Client()

    def test_paginator(self):
        urls = {
            MAIN_URL: settings.MAX_POSTS,
            MAIN_PAGE_PAGINATOR_SECOND: POSTS_SECOND_PAGE,
            GROUP_URL: settings.MAX_POSTS,
            GROUP_LIST_PAGINATOR_SECOND: POSTS_SECOND_PAGE,
            PROFILE_URL: settings.MAX_POSTS,
            PROFILE_PAGINATOR_SECOND: POSTS_SECOND_PAGE,
        }
        for url, number in urls.items():
            with self.subTest(url=url):
                response = self.guest.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), number
                )
