from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
STRING_FROM_POST = 'author: {}, date: {:%m%d%Y}, group: {}, text: {:.15}'


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Наименование группы, не более 200 символов'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Уникальный фрагмент URL',
        help_text='Используется как стандарт записи ссылок на объект'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Опишите группу как можно подробнее'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Основной текст поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Заполняется автоматически, в момент создания поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        # Аргумент upload_to указывает директорию,
        # в которую будут загружаться пользовательские файлы.
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return STRING_FROM_POST.format(
            self.author.username,
            self.pub_date,
            self.group,
            self.text,
        )


class Comment(models.Model):
    COMMENT_TEXT_LEN = 15
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Текст поста',
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='Автор',
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Введите текст комментария'
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        return self.text[:Comment.COMMENT_TEXT_LEN]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'follow'
        verbose_name_plural = 'follows'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique subscription'
            ),
        )

    def __str__(self):
        return (
            f'Follower: {self.user.username} ({self.user.id}); '
            f'Following to: {self.author.username} ({self.author.id})'
        )
