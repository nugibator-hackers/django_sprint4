from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.http import Http404
from django.views.generic import (ListView,
                                  CreateView,
                                  UpdateView,
                                  DeleteView,
                                  DetailView)

from .models import Post, Category, User, Comment
from .forms import PostForm, CommentForm, UserForm


NUMBER_POSTS = 10


def get_posts(posts=Post.objects, filters=True, annotations=True):
    queryset = posts.select_related(
        'author',
        'location',
        'category'
    )
    if filters:
        queryset = queryset.filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    if annotations:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
    return queryset


class CommentMixin(LoginRequiredMixin, UserPassesTestMixin):
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, id=comment_id)

    def get_success_url(self):
        post_id = self.kwargs.get('post_id')
        return reverse('blog:post_detail', kwargs={'pk': post_id})

    def test_func(self):
        comment = self.get_object()
        return comment.author == self.request.user


def profile(request, user_name):
    user = get_object_or_404(User, username=user_name)
    posts = (
        get_posts(filters=False).filter(author=user)
    )
    paginator = Paginator(posts, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = NUMBER_POSTS

    def get_queryset(self):
        post_list = get_posts()
        return post_list


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_id = kwargs['pk']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', pk=self.post_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        if not post.is_published and post.author != self.request.user:
            raise Http404
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])

    def dispatch(self, request, *args, **kwargs):
        self.post_id = kwargs['pk']
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', pk=self.post_id)
        return super().dispatch(request, *args, **kwargs)


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = NUMBER_POSTS

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['category_slug'], is_published=True
        )
        return get_posts(filters=False).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category=self.category,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category

        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user.username])


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['pk'],
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'pk': self.kwargs['pk']}
        )


class CommentDeleteView(CommentMixin, DeleteView):
    pass


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm
