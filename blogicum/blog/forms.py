from .models import Post, User, Comment

from django import forms


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'created_at')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
