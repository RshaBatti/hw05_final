from .models import Post, Comment, Follow
from django import forms
from django.forms import ModelForm, CharField


class PostForm(ModelForm):
    class Meta:
        model = Post

        fields = ("text", "group", 'image')
        help_texts = {'text': 'Текст Вашей записи',
                      'group': 'Выберите группу (необязательно)',
                      'image': 'Загрузите картинку'}
        labels = {'text': 'Текст',
                  'group': 'Группа',
                  'image': 'Картинка'}


class CommentForm(ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ("text",)


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow

        fields = ('user',)
