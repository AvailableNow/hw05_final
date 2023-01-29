from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow


def paginator_page(post_list, request):
    return Paginator(
        post_list, settings.MAX_POSTS
    ).get_page(request.GET.get('page'))


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': paginator_page(Post.objects.all(), request),
    })


def group_posts(request, slug):
    """Получение постов нужной группы по запросу"""
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': paginator_page(group.posts.all(), request)
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    follow = (
        request.user.is_authenticated
        and request.user.username != username
        and Follow.objects.filter(
            author=author,
            user=request.user
        ).exists()
    )
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': paginator_page(author.posts.all(), request),
        'following': follow
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': CommentForm(),
    })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form
        })
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:profile', username=post.author)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
            'post': post,
        })
    form.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(request, 'posts/follow.html', {
        'page_obj': paginator_page(
            Post.objects.filter(author__following__user=request.user),
            request
        )
    })


@login_required
def profile_follow(request, username):
    if not (request.user.username == username or Follow.objects.filter(
            author__username=username, user=request.user).exists()):
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username)
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username).delete()
    return redirect('posts:profile', username)
