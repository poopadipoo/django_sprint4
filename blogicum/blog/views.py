from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .filters import (
    can_view_post, filter_posts_for_profile, get_published_posts
)
from .forms import CommentForm, PostForm
from .models import Category, Comment, Post
from .utils import paginate_queryset


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if not form.instance.pub_date:
            form.instance.pub_date = timezone.now()
        messages.success(self.request, 'Пост успешно создан!')
        return super().form_valid(form)

    def get_initial(self):
        return {'pub_date': timezone.now().date()}

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.object = self.get_object()
        if self.object.author != request.user:
            return redirect('blog:post_detail', post_id=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk},
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.object = self.get_object()
        if self.object.author != request.user:
            return redirect('blog:post_detail', post_id=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy('blog:index')


class CommentPermissionMixin(LoginRequiredMixin):
    model = Comment
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs.get(self.pk_url_kwarg),
            post_id=self.kwargs.get('post_id'),
        )

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.object = self.get_object()
        if self.object.author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs.get('post_id'),
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.object.post_id},
        )


class CommentUpdateView(CommentPermissionMixin, UpdateView):
    form_class = CommentForm
    template_name = 'blog/comment.html'


class CommentDeleteView(CommentPermissionMixin, DeleteView):
    template_name = 'blog/comment.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        return context


def index(request):
    post_list = get_published_posts(Post)
    page_obj = paginate_queryset(post_list, request, per_page=10)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'location', 'category'),
        id=post_id,
    )
    if not can_view_post(post, request.user):
        raise Http404('Пост не найден')

    context = {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.select_related(
            'author'
        ).order_by('created_at'),
        'now': timezone.now(),
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    post_list = get_published_posts(Post).filter(category=category)
    page_obj = paginate_queryset(post_list, request, per_page=10)
    context = {'page_obj': page_obj, 'category': category}
    return render(request, 'blog/category.html', context)


class UserProfileView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        self.profile_user = get_object_or_404(
            User,
            username=self.kwargs.get('username'),
        )
        is_owner = (
            self.request.user.is_authenticated
            and self.request.user == self.profile_user
        )
        posts = Post.objects.select_related(
            'author',
            'location',
            'category',
        ).filter(
            author=self.profile_user,
        ).order_by('-pub_date')
        return filter_posts_for_profile(posts, is_owner)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile_user
        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    fields = ['first_name', 'last_name', 'username', 'email']

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен!')
        return super().form_valid(form)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.success(request, 'Ваш комментарий успешно добавлен!')
            return redirect('blog:post_detail', post_id=post_id)
        messages.error(request, 'Ошибка при добавлении комментария')

    return redirect('blog:post_detail', post_id=post_id)
