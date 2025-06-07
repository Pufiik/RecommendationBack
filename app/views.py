import numpy as np
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, Count, Case, When
from django.views.decorators.http import require_http_methods

from app.faiss_index import FaissIndex
from app.forms import LoginForm
from app.models import Article, ArticleInteraction
from app.serialization import ArticleSerializer
from recommend_back import settings

N = 2


def index(request):
    return render(request, 'layouts/base.html')


@login_required
def profile_edit(request):
    def popular_articles(n=5):
        return (
            Article.objects
            .annotate(
                like_count=Count(
                    'interactions',
                    filter=Q(interactions__vote=ArticleInteraction.LIKE)
                )
            )
            .order_by('-like_count', '-created_at')[:n]
        )

    qs = popular_articles()
    items = []
    profile = request.user.profile
    for art in qs:
        liked = ArticleInteraction.objects.filter(
            user_profile=profile,
            article=art,
            vote=ArticleInteraction.LIKE
        ).exists()
        items.append({
            'id': art.id,
            'title': art.title,
            'annotation': art.annotation,
            'like_count': art.like_count,
            'liked': liked,
        })

        print(items)

    return render(request, 'profile/edit.html', {'popular': items})


def logout(request):
    auth.logout(request)
    return redirect(reverse('login'))


@csrf_protect
def login(request):
    if request.method == "POST":

        form = LoginForm(request.POST)

        if form.is_valid():
            user = auth.authenticate(request, **form.cleaned_data)
            if user:
                auth.login(request, user)
                return redirect(reverse('profile.edit'))

    return render(request, 'login.html', context={'form': LoginForm()})


@login_required
def recommend(request):
    profile = request.user.profile
    vec = profile.embedding
    read_ids = profile.interactions.values_list('article_id', flat=True)

    if settings.USE_FAISS:
        ids_scores = FaissIndex.search(vec, top_k=N)
        ids = [i for i, _ in ids_scores if i not in read_ids]
        qs = (
            Article.objects
            .filter(id__in=ids)
            .annotate(
                like_count=Count(
                    'interactions',
                    filter=Q(interactions__vote=ArticleInteraction.LIKE)
                )
            )
        )

        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(ids)])
        qs = qs.order_by(preserved)

    else:
        all_candidates = Article.objects.exclude(id__in=read_ids)

        def cosine(a, b):
            a_np = np.array(a, dtype='float32')
            b_np = np.array(b, dtype='float32')
            return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

        scored = [(article, cosine(article.embedding, vec)) for article in all_candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        top_articles = [article for article, _ in scored[:N]]
        top_ids = [a.id for a in top_articles]

        qs = (
            Article.objects
            .filter(id__in=top_ids)
            .annotate(
                like_count=Count(
                    'interactions',
                    filter=Q(interactions__vote=ArticleInteraction.LIKE)
                )
            )
        )
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(top_ids)])
        qs = qs.order_by(preserved)

    data = ArticleSerializer(qs, many=True, context={'request': request}).data
    return render(request, 'profile/recommend.html', {'items': data})


@login_required
def toggle_like(request, pk):
    article = get_object_or_404(Article, pk=pk)
    profile = request.user.profile
    try:
        inter = ArticleInteraction.objects.get(user_profile=profile, article=article)
        print(1)
        print(inter)
        inter.delete()
    except ArticleInteraction.DoesNotExist:
        ArticleInteraction.objects.create(
            user_profile=profile,
            article=article,
            vote=ArticleInteraction.LIKE
        )
    return redirect(reverse('profile.edit'))
