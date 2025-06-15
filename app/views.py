from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, Count, Case, When, Value, IntegerField, FilteredRelation
from .constants import N
from app.faiss_index import FaissIndex
from app.forms import LoginForm
from app.models import Article, ArticleInteraction
from app.serialization import ArticleSerializer
from app.utils import get_cosine_similar_ids
from recommend_back import settings


@login_required
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    print(len(article.embedding))
    like_count = ArticleInteraction.objects.filter(
        article=article, vote=ArticleInteraction.LIKE
    ).count()
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ArticleInteraction.objects.filter(
            user_profile=request.user.profile,
            article=article,
            vote=ArticleInteraction.LIKE
        ).exists()

    return render(request, 'article/details.html', {
        'article': article,
        'like_count': like_count,
        'user_liked': user_liked,
    })


@login_required
def profile_edit(request, n=5):
    profile = request.user.profile
    qs = Article.objects.annotate(
        user_inter=FilteredRelation(
            'interactions',
            condition=Q(interactions__user_profile=profile)
        )
    )

    qs = qs.annotate(
        like_count=Count(
            'interactions',
            filter=Q(interactions__vote=ArticleInteraction.LIKE),
        )
    )

    qs = qs.annotate(
        user_vote=Coalesce('user_inter__vote', Value(0), output_field=IntegerField())
    )

    qs = qs.order_by('-user_vote', '-like_count', '-created_at')[:n]
    serializer = ArticleSerializer(qs, many=True, context={'request': request})
    data = serializer.data

    return render(request, 'profile/edit.html', {'popular': data})


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
    read_ids = list(profile.interactions.values_list('article_id', flat=True))

    if settings.USE_FAISS:
        ids_scores = FaissIndex.search(profile.embedding, top_k=N + len(read_ids))
        ids = [i for i, _ in ids_scores if i not in read_ids][:N]
    else:
        ids = get_cosine_similar_ids(
            query_vec=profile.embedding,
            exclude_ids=read_ids,
            top_k=N,
        )

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

    data = ArticleSerializer(qs, many=True, context={'request': request}).data
    return render(request, 'profile/recommend.html', {'items': data})


def home(request):
    if request.user.is_authenticated:
        return redirect('profile.edit')
    return redirect('login')


@login_required
def toggle_like(request, pk):
    article = get_object_or_404(Article, pk=pk)
    profile = request.user.profile
    try:
        inter = ArticleInteraction.objects.get(user_profile=profile, article=article)
        inter.delete()
    except ArticleInteraction.DoesNotExist:
        ArticleInteraction.objects.create(
            user_profile=profile,
            article=article,
            vote=ArticleInteraction.LIKE
        )
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def similar_articles(request, pk):
    article = get_object_or_404(Article, pk=pk)
    profile = request.user.profile

    user_liked = ArticleInteraction.objects.filter(
        user_profile=profile,
        article=article,
        vote=ArticleInteraction.LIKE
    ).exists()
    like_count = ArticleInteraction.objects.filter(
        article=article,
        vote=ArticleInteraction.LIKE
    ).count()

    lang = request.GET.get('lang', 'all')
    if lang in (Article.RU, Article.ENG):
        allowed_ids = set(
            Article.objects
            .filter(language=lang)
            .values_list('id', flat=True)
        )
    else:
        allowed_ids = None

    if settings.USE_FAISS:
        raw = FaissIndex.search(article.embedding, top_k=N + 1)
        candidates = [i for i, _ in raw if i != article.id]
    else:
        candidates = get_cosine_similar_ids(
            query_vec=article.embedding,
            exclude_ids={article.id},
            top_k=N,
            filter_ids=allowed_ids
        )

    if allowed_ids is None:
        similar_ids = candidates[:N]
    else:
        similar_ids = [i for i in candidates if i in allowed_ids][:N]

    if not similar_ids:
        similar = []
    else:
        qs = (
            Article.objects
            .filter(id__in=similar_ids)
            .annotate(
                like_count=Count(
                    'interactions',
                    filter=Q(interactions__vote=ArticleInteraction.LIKE)
                )
            )
        )

        preserved = Case(*[
            When(pk=pk_, then=pos) for pos, pk_ in enumerate(similar_ids)
        ], output_field=IntegerField())
        qs = qs.order_by(preserved)

        similar = []
        for art in qs:
            liked_flag = ArticleInteraction.objects.filter(
                user_profile=profile,
                article=art,
                vote=ArticleInteraction.LIKE
            ).exists()
            similar.append({
                'id': art.id,
                'title': art.title,
                'annotation': art.annotation,
                'like_count': art.like_count,
                'liked': liked_flag,
            })

    return render(request, 'article/details.html', {
        'article': article,
        'user_liked': user_liked,
        'like_count': like_count,
        'similar': similar,
        'lang': lang,
    })
