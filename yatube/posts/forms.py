from .models import Comment, Post

from django.forms import ModelForm


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Введите текст',
            'group': 'Выберите нужную группу',
            'image': 'Выберите изображение'
        }
        help_text = {
            'text': 'Придумайте текст для поста. '
                    'Поле обязательно для заполнения',
            'group': 'Группа поста',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
