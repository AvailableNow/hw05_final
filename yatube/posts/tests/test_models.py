from django.test import TestCase

from ..models import Comment, Group, Post, User, Follow
from ..models import STRING_FROM_POST, STRING_FROM_COMMENT, STRING_FROM_FOLLOW


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Комментарий',
            post=cls.post,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user
        )

    def test_verbose_name(self):
        field_verboses_post = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses_post.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).verbose_name, expected
                )

        field_verboses_group = {
            'title': 'Название',
            'slug': 'Уникальный фрагмент URL',
            'description': 'Описание'
        }
        for value, expected in field_verboses_group.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Group._meta.get_field(value).verbose_name, expected
                )

        field_verboses_comment = {
            'text': 'Текст комментария',
            'author': 'Автор',
            'post': 'Комментаруемый пост',
            'pub_date': 'Дата публикации'
        }
        for value, expected in field_verboses_comment.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Comment._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        field_help_text_post = {
            'text': 'Основной текст поста',
            'pub_date': 'Заполняется автоматически, в момент создания поста',
        }
        field_help_text_group = {
            'slug': 'Используется как стандарт записи ссылок на объект',
            'description': 'Опишите группу как можно подробнее',
            'title': 'Наименование группы, не более 200 символов',
        }
        field_help_text_comment = {
            'post': 'Пост к которому создается комментарий',
            'text': 'Введите текст комментария',
        }

        for value, expected in field_help_text_post.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).help_text, expected
                )
        for value, expected in field_help_text_group.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Group._meta.get_field(value).help_text, expected
                )
        for value, expected in field_help_text_comment.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Comment._meta.get_field(value).help_text, expected
                )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(STRING_FROM_POST.format(
            self.post.author.username,
            self.post.pub_date,
            self.post.group,
            self.post.text,
        ), str(self.post)
        )
        self.assertEqual(STRING_FROM_COMMENT.format(
            self.comment.author.username,
            self.comment.pub_date,
            self.comment.post,
            self.comment.text,
        ), str(self.comment)
        )
        self.assertEqual(STRING_FROM_FOLLOW.format(
            self.follow.author.username,
            self.follow.author.id,
            self.follow.user.username,
            self.user.id), str(self.follow)
        )
        self.assertEqual(self.group.title, str(self.group))
