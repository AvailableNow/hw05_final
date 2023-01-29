import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Comment, Group, Post, User

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
POST_TEST = 'ш' * 50

NEW_POST_URL = reverse('posts:post_create')
NIK = 'testauthor_1'
NIK_2 = 'testauthor_2'
PROFILE_URL = reverse(
    'posts:profile',
    args=[NIK]
)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)
UPLOADED2 = SimpleUploadedFile(
    name='small_2.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)
UPLOADED3 = SimpleUploadedFile(
    name='small_3.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


# Для сохранения media-файлов в тестах будет использоватьсяgs
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем записи в базе данных
        cls.user = User.objects.create_user(username=NIK)
        cls.username = cls.user.username
        cls.user_2 = User.objects.create_user(username=NIK_2)
        cls.username_2 = cls.user_2.username
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='новая группа',
            slug='test_slug2',
            description='Тест-описание2'
        )

        # Создадим запись в БД
        cls.post = Post.objects.create(
            text=POST_TEST,
            group=cls.group,
            author=cls.user,
            image=UPLOADED,
        )

        cls.POST_PAGE_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id]
        )
        cls.EDIT_POST_URL = reverse(
            'posts:post_edit',
            args=[cls.post.id]
        )
        cls.COMMENT_ADD_URL = reverse('posts:add_comment',
                                      args=[cls.post.id])
        # первый клиент автор поста
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        # второй клиент не автор поста
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_2)

    # Удаляем временную папку
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    # Тест для проверки формы создания нового поста (create_post)
    def test_create_post(self):
        """Проверка, что валидная форма создаёт пост"""
        form_data = {
            'text': 'тестовая публикация',
            'group': self.group_2.pk,
            'image': UPLOADED2,
        }
        # Подсчитаем количество записей в Post
        posts_before = set(Post.objects.all())
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        posts_after = set(Post.objects.all())
        self.assertEqual(len(posts_after.difference(posts_before)), 1)
        post = list(posts_after.difference(posts_before))[0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(post.image, f'posts/{form_data["image"]}')

    def test_post_edit_by_author(self):
        """Выполнение редактирование поста автором"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Автор, редактирует пост',
            'group': self.group_2.pk,
            'image': UPLOADED3
        }
        response = self.authorized_client.post(
            self.EDIT_POST_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, self.POST_PAGE_URL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, f'posts/{form_data["image"]}')

    def test_post_edit_by_non_author(self):
        """Редактирование поста не автором поста
        невозможно"""
        form_data = {
            'text': 'это сообщение не должно переписаться в пост',
            'group': self.group.pk,
            'image': UPLOADED
        }
        response = self.authorized_client_2.post(
            self.EDIT_POST_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)

    def test_authorized_comment_create(self):
        """"Проверка создания комментария"""
        comments_count = Comment.objects.all().count()
        form_data = {
            'text': 'New comment',
            'author': self.user,
        }
        response = self.authorized_client.post(
            self.COMMENT_ADD_URL,
            data=form_data,
            follow=True
        )
        comment = Comment.objects.get(pk=self.post.pk)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response, self.POST_PAGE_URL)
        self.assertEqual(comment.text, form_data['text'])

    def test_guest_user_cannot_create_comment(self):
        """"Проверка неавторизованный пользователь не может комментировать"""
        comments_count = Comment.objects.all().count()
        form_data = {
            'text': 'TEST',
            'author': self.user,
        }
        response = self.guest_client.post(
            self.COMMENT_ADD_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(response.status_code, 200)
