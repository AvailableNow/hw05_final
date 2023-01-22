import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User, Follow

POSTS_SECOND_PAGE = 3
MAIN_URL = reverse('posts:index')
MAIN_PAGE_PAGINATOR_SECOND = MAIN_URL + '?page=2'
SLUG_1 = 'testslug_1'
NIK_1 = 'testauthor_1'
SLUG_2 = 'test_slug_2'
NIK_2 = 'testauthor_2'
NIK_3 = 'testauthor_3'
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
            author=cls.user,
            image=SMALL_GIF
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
            self.assertEqual(self.post.image, post.image)

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
            with self.subTest(url=url, number=number):
                response = self.guest.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), number
                )


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username=NIK_1
        )
        cls.user2 = User.objects.create_user(
            username=NIK_2
        )
        cls.author = User.objects.create_user(
            username=NIK_3
        )

        cls.FOLLOW_URL = reverse(
            'posts:profile_follow', kwargs={'username': cls.author.username}
        )
        cls.UNFOLLOW_URL = reverse(
            'posts:profile_unfollow', kwargs={'username': cls.author.username}
        )
        cls.PROFILE_URL = reverse('posts:profile',
                                  kwargs={'username':
                                          cls.author.username})
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)
        cls.form_data = {'user': cls.user,
                         'author': cls.author}
        cls.test_post = Post.objects.create(author=cls.author,
                                            text='Текстовый текст')

    def test_auth_user_can_follow(self):
        """Тест авторизованный пользователь может
        подписываться."""
        count_followers = Follow.objects.all().count()
        response = self.authorized_client.post(
            self.FOLLOW_URL,
            data=self.form_data,
            follow=True
        )
        final_follow = Follow.objects.all().count() - 1
        self.assertEqual(count_followers, final_follow)
        self.assertRedirects(response, self.PROFILE_URL)

    def test_auth_user_can_unfollow(self):
        """Тест авторизованный пользователь может
        отписаться."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        count_followers = Follow.objects.all().count()
        unfollow = self.authorized_client.post(
            self.UNFOLLOW_URL,
            data=self.form_data,
            follow=True
        )
        final_follow = Follow.objects.all().count() + 1
        self.assertEqual(count_followers, final_follow)
        self.assertRedirects(unfollow, self.PROFILE_URL)

    def test_follower_see_new_post(self):
        """У подписчика появляется новый пост автора.
        А у не подписчика его нет"""
        Follow.objects.create(user=self.user,
                              author=self.author)
        response_follow = self.authorized_client.get(
            reverse('posts:follow_index'))
        posts_follow = response_follow.context['page_obj']
        self.assertIn(self.test_post, posts_follow)

    def test_follower_not_see_new_post(self):
        """У не подписчика не появляется новый пост автора."""
        Follow.objects.create(user=self.user,
                              author=self.author)
        response_no_follower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        posts_no_follow = response_no_follower.context['page_obj']
        self.assertNotIn(self.test_post, posts_no_follow)
