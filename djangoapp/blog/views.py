from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import Http404, HttpRequest, HttpResponse
from django.views.generic import ListView
from blog.models import Post, Page

PER_PAGE = 9

class PostListView(ListView):
    template_name = "blog/pages/index.html"
    context_object_name = "posts"
    paginate_by = PER_PAGE
    queryset = Post.objects.get_published()

    # overriding the get_context_data() of ListView()
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Home - "
        })
        return context


def post(request, slug):
    post_obj = Post.objects.get_published().filter(slug=slug).first()

    if post_obj is None:
        raise Http404()
    
    page_title = f"{post_obj.title} Post - "

    return render(
        request,
        "blog/pages/post.html",
        {
            "post": post_obj,
            "page_title": page_title,
        }
    )

def page(request, slug):
    page_obj = Page.objects.get_published().filter(slug=slug).first()

    if page_obj is None:
        raise Http404()
    
    page_title = f"{page_obj.title} Page - "

    return render(
        request,
        "blog/pages/page.html",
        {
            "page": page_obj,
            "page_title": page_title,

        }
    )


class CreatedByListView(PostListView):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._temp_context: dict[str, Any] = {}

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        author_pk = self.kwargs.get("author_pk")
        user = User.objects.filter(pk=author_pk).first()

        if user is None:
            raise Http404
        
        self._temp_context.update(
            {
                "author_pk": author_pk,
                "user": user,
            }
        )
        
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        qs = qs.filter(created_by__pk=self._temp_context["user"].pk)
        return qs
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        user = self._temp_context["user"]
        user_full_name = user.username

        if user.first_name:
            user_full_name = f"{user.first_name} {user.last_name} "
        
        page_title = f"Posts by {user_full_name} - "
        ctx.update(
            {
                "page_title": page_title,
            }
        )

        return ctx


class CategoryListView(PostListView):
    allow_empty = False

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset().filter(category__slug=self.kwargs.get("slug"))
        return qs
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page_title = f"{self.object_list[0].category} Category - "
        context.update(
            {
                "page_title": page_title,
            }
        )
        return context


class TagListView(PostListView):
    allow_empty = False

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().filter(tags__slug=self.kwargs.get("slug"))
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs.get("slug")
        tag_name = self.object_list[0].tags.filter(slug=tag_slug).first()
        page_title = f"{tag_name} Tag - "
        context.update(
            {
                "page_title": page_title,
            }
        )
        return context


def search(request):
    search_value = request.GET.get("search", "").strip()
    posts_obj = Post.objects.get_published().filter(
        Q(title__icontains=search_value) | 
        Q(excerpt__icontains=search_value) | 
        Q(content__icontains=search_value)
    )[:PER_PAGE]
    
    page_title = f"{search_value[:15]} Search - "

    return render(
        request,
        "blog/pages/index.html",
        {
            "page_obj": posts_obj,
            "search_value": search_value,
            "page_title": page_title,
        },
    )