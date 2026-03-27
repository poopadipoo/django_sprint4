from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginate_queryset(queryset, request, per_page=10):
    """
    Универсальная функция для пагинации любого queryset'а.
    """
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # Если page не число, показываем первую страницу
        page_obj = paginator.get_page(1)
    except EmptyPage:
        # Если страница пуста, показываем последнюю
        page_obj = paginator.get_page(paginator.num_pages)

    return page_obj