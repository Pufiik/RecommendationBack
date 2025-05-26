import numpy as np
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import F
from pgvector.django import CosineDistance

from app.faiss_index import FaissIndex
from app.forms import LoginForm
from app.models import Article
from app.serialization import ArticleSerializer
from recommend_back import settings

N = 2


def index(request):
    return render(request, 'layouts/base.html')


@login_required
def profile_edit(request):
    return render(request, 'profile/edit.html')


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
    print(vec)
    print(read_ids)

    if settings.USE_FAISS:
        ids_scores = FaissIndex.search(vec, top_k=N)
        print(ids_scores)
        ids = [i for i, _ in ids_scores if i not in read_ids]
        print(ids)
        qs = Article.objects.filter(id__in=ids)
        print(qs)
    else:
        print(1)
        all_candidates = Article.objects.exclude(id__in=read_ids)

        def cosine(a, b):
            a_np = np.array(a, dtype='float32')
            b_np = np.array(b, dtype='float32')
            return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))

        scored = [(article, cosine(article.embedding, vec)) for article in all_candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        qs = [article for article, _ in scored[:10]]

    data = ArticleSerializer(qs, many=True).data
    print('data')
    print(data)
    return render(request, 'profile/help.html', context={'data': data})
