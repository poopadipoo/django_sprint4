from django.db.models import Count
from django.utils import timezone


def get_published_posts(PostModel):
    """Return published posts with related objects and comment count."""
    return PostModel.objects.select_related(
        'author',
        'location',
        'category',
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def add_comment_count(queryset):
    """Add comments counter to a queryset before pagination."""
    return queryset.annotate(comment_count=Count('comments'))


def filter_posts_for_profile(posts, is_owner):
    """Filter profile posts depending on whether current user is the owner."""
    if not is_owner:
        posts = posts.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
    return add_comment_count(posts)


def can_view_post(post, user):
    """Check whether a post can be viewed by a user."""
    is_author = user.is_authenticated and user == post.author
    if is_author:
        return True
    return (
        post.is_published
        and post.category.is_published
        and post.pub_date <= timezone.now()
    )
