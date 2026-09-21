import json
import random
import uuid
import csv
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import re

from .items_data import ITEMS
from .content_model import recommender
from .models import Session, ClickEvent, Rating

ITEM_BY_ID = {item["id"]: item for item in ITEMS}
UNIQUE_CATEGORIES = sorted(set(item["category"] for item in ITEMS))
MODES = ["static", "random", "personalized"]


def index(request):
    return render(request, "recommender/index.html")


@csrf_exempt
def api_session_start(request):
    data = json.loads(request.body) if request.body else {}
    raw_name = data.get("name", "").strip() or "guest"
    
    # naam ko clean karo — sirf letters/numbers/underscore rakho, session_id ke liye safe banane ke liye
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', raw_name).strip('_').lower() or "guest"
    session_id = f"{slug}_{uuid.uuid4().hex[:4]}"  # duplicate naam ho to bhi unique rahega

    mode_order = MODES.copy()
    first_two = ["static", "random"]
    random.shuffle(first_two)
    mode_order = first_two + ["personalized"]
    targets = {m: random.choice(UNIQUE_CATEGORIES) for m in mode_order}

    Session.objects.create(
        session_id=session_id,
        participant_name=raw_name,
        mode_order=",".join(mode_order),
        age_range=data.get("age_range", ""),
        web_familiarity=data.get("web_familiarity", ""),
    )
    return JsonResponse({"session_id": session_id, "mode_order": mode_order, "targets": targets})

def api_items(request):
    return JsonResponse(ITEMS, safe=False)


def api_items_random(request):
    shuffled = ITEMS.copy()
    random.shuffle(shuffled)
    return JsonResponse(shuffled, safe=False)


def api_recommendations(request):
    session_id = request.GET.get("session_id", "guest")
    clicked = list(ClickEvent.objects.filter(session_id=session_id).values_list("item_id", flat=True))
    ranked_ids = recommender.recommend(clicked)
    ranked_items = [ITEM_BY_ID[i] for i in ranked_ids if i in ITEM_BY_ID]
    return JsonResponse(ranked_items, safe=False)


@csrf_exempt
def api_click(request):
    data = json.loads(request.body)
    session_id = data.get("session_id", "guest")
    mode = data.get("mode", "static")
    item_id = data.get("item_id")
    is_target = bool(data.get("is_target", False))
    time_taken_ms = data.get("time_taken_ms")

    if item_id not in ITEM_BY_ID:
        return JsonResponse({"error": "invalid item_id"}, status=400)

    ClickEvent.objects.create(
        session_id=session_id,
        mode=mode,
        item_id=item_id,
        category=ITEM_BY_ID[item_id]["category"],
        is_target=is_target,
        time_taken_ms=time_taken_ms,
    )
    return JsonResponse({"status": "ok"})


@csrf_exempt
def api_rating(request):
    data = json.loads(request.body)
    session_id = data.get("session_id", "guest")
    mode = data.get("mode", "static")
    relevance = data.get("relevance")
    ease = data.get("ease")

    if relevance not in [1, 2, 3, 4, 5] or ease not in [1, 2, 3, 4, 5]:
        return JsonResponse({"error": "relevance and ease must be 1-5"}, status=400)

    Rating.objects.create(session_id=session_id, mode=mode, relevance=relevance, ease=ease)
    return JsonResponse({"status": "ok"})


def api_log(request):
    events = list(ClickEvent.objects.values(
        "session_id", "mode", "item_id", "category", "is_target", "time_taken_ms", "created_at"
    ))
    return JsonResponse(events, safe=False)


def api_ratings_log(request):
    ratings = list(Rating.objects.values("session_id", "mode", "relevance", "ease", "created_at"))
    return JsonResponse(ratings, safe=False)

def export_clicks_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="all_clicks.csv"'
    writer = csv.writer(response)
    writer.writerow(["name", "session_id", "mode", "item_id", "category", "is_target", "time_taken_ms", "created_at"])

    for event in ClickEvent.objects.all().order_by("created_at"):
        name = get_participant_name(event.session_id)
        writer.writerow([name, event.session_id, event.mode, event.item_id, event.category, event.is_target, event.time_taken_ms, event.created_at])

    return response


def export_ratings_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="all_ratings.csv"'
    writer = csv.writer(response)
    writer.writerow(["name", "session_id", "mode", "relevance", "ease", "created_at"])

    for rating in Rating.objects.all().order_by("created_at"):
        name = get_participant_name(rating.session_id)
        writer.writerow([name, rating.session_id, rating.mode, rating.relevance, rating.ease, rating.created_at])

    return response


def get_participant_name(session_id):
    session = Session.objects.filter(session_id=session_id).first()
    return session.participant_name if session else "unknown"