# blog/utils/filters.py
from django.utils import timezone
from django.db.models import Count

def get_published_posts(PostModel):
    """
    Возвращает QuerySet опубликованных постов с аннотацией комментариев.
    """
    return PostModel.objects.select_related(
        'author',
        'location',
        'category'
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True
    ).order_by(
        '-pub_date'
    ).annotate(comment_count=Count('comments'))

def filter_posts_for_profile(posts, is_owner):
    """
    Фильтрует посты для профиля в зависимости от прав доступа.
    """
    if is_owner:
        return posts
    else:
        return posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )

def can_view_post(post, user):
    """
    Проверяет, может ли пользователь видеть пост.
    """
    is_author = user.is_authenticated and user == post.author
    
    if is_author:
        return True
    
    return (post.is_published and 
            post.category.is_published and 
            post.pub_date <= timezone.now())