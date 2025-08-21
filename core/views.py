import random
import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from .models import Aid
import geoip2.database
import os
import re
from user_agents import parse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_DB_PATH = os.path.join(BASE_DIR, "core", "geo", "GeoLite2-City.mmdb")
reader = geoip2.database.Reader(GEO_DB_PATH)


def worker_request(request):
    aid_param = request.GET.get("aid")
    if not aid_param:
        return JsonResponse({"error": "aid is required"}, status=400)

    aid = get_object_or_404(Aid, aid=aid_param)
    if not hasattr(aid, "campaign"):
        return JsonResponse({"error": "No campaign attached to this aid"}, status=404)

    campaign = aid.campaign
    params = {k: v[0] for k, v in dict(request.GET).items()}

    # --- GEO ---
    geo_related = ["geo_lat", "geo_lon", "geo_country"]
    need_geo = any(not params.get(f) or params.get(f).startswith("{") for f in geo_related)
    if need_geo:
        uip = params.get("uip")
        if uip:
            try:
                response = reader.city(uip)
                params["geo_lat"] = response.location.latitude
                params["geo_lon"] = response.location.longitude
                params["geo_country"] = response.registered_country.iso_code
            except Exception:
                for f in geo_related:
                    params.setdefault(f, None)

    # --- UA ---
    ua_string = params.get("ua", "")
    ua = parse(ua_string)
    if not params.get("device_os") or params.get("device_os").startswith("{"):
        params["device_os"] = f"{ua.os.family} {ua.os.version_string}"
    if not params.get("device_category") or params.get("device_category").startswith("{"):
        params["device_category"] = (
            "mobile" if ua.is_mobile else "tablet" if ua.is_tablet else "desktop"
        )
    if not params.get("device_make") or params.get("device_make").startswith("{"):
        params["device_make"] = ua.device.brand or ""
    if not params.get("device_model") or params.get("device_model").startswith("{"):
        params["device_model"] = ua.device.model or ""

    print(
        f'\n{params.get("device_os"), params.get("device_category"), params.get("device_model"), params.get("device_make")}')
    print(f'{params.get("geo_lat"), params.get("geo_lon"), params.get("geo_country")}\n')

    # --- VAST VERSION ---
    params["vast_version"] = "4"
    params["adid"] = ''.join(random.choices('0123456789ABCDEF', k=16))

    # --- URL ---
    placeholders = set(re.findall(r"{(.*?)}", campaign.url_template))
    final_params = {key: params.get(key, f"{{{key}}}") for key in placeholders}

    try:
        final_url = campaign.url_template.format(**final_params)
    except KeyError as e:
        return JsonResponse({"error": f"missing campaign placeholder {str(e)}"}, status=400)

    # return JsonResponse({"url": final_url}, status=200)

    print(final_url)

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "User-Agent": params.get("ua", ""),
        "X-Forwarded-For": params.get("uip", ""),
        "Origin": f"https://{params.get('app_domain', '')}",
        "Referer": f"https://{params.get('app_domain', '')}/",
        "Cookie": f"vmuid={params.get('cb', '')}",
        "Host": "s.adtelligent.com"
    }
    try:
        resp = requests.get(final_url)
    except requests.RequestException as e:
        return JsonResponse({"error": f"request failed: {str(e)}"}, status=502)

    return HttpResponse(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get("Content-Type", "text/plain"),
    )
