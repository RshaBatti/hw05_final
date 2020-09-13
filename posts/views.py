from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  'index.html',
                  {'page': page,
                   'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts_group.all()
    paginator = Paginator(group_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  'group.html',
                  {'group': group,
                   'page': page,
                   'paginator': paginator})


@login_required()
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'new_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(author=author)
    follow = following.count()
    follower = Follow.objects.filter(user=author).count()
    post = author.posts.all()
    count = post.count()
    paginator = Paginator(post, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {'page': page,
                                            'paginator': paginator,
                                            'author': author,
                                            'count': count,
                                            'post': post,
                                            'following': following,
                                            'follow': follow,
                                            'follower': follower})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    post_list = post.author.posts.all()
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    form = CommentForm(instance=None)
    page = paginator.get_page(page_number)
    items = post.comments.all()
    response = render(request,
                      'post.html',
                      {
                          "author": post.author,
                          'items': items,
                          "post": post,
                          'form': form,
                          'page': page,
                          'paginator': paginator
                      }
                      )
    return response


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)

    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=request.user.username,
                        post_id=post_id)

    return render(
        request, 'new_post.html', {'form': form, 'post': post},
    )


def page_not_found(request, exception):
    return render(
        request,
        "404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request,
                  'follow.html',
                  {'page': page,
                   'paginator': paginator})


@login_required
def profile_follow(request, username):
    follower_user = request.user
    following_author = get_object_or_404(User, username=username)
    subscription = Follow.objects.filter(user=follower_user,
                                         author=following_author)
    if not username == follower_user.username and not subscription:
        Follow.objects.create(user=follower_user, author=following_author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    follower_user = request.user
    following_author = get_object_or_404(User, username=username)
    subscription = Follow.objects.filter(user=follower_user,
                                         author=following_author)
    subscription.delete()
    return redirect('profile', username=username)
