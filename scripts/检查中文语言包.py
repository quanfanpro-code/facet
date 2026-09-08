"""检查简体中文语言注册、词条、占位符和实际 HTTP 接口。"""
import json
from collections import Counter
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from i18n import LANGUAGES


def flatten(data, prefix=""):
    result = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, path))
        else:
            result[path] = value
    return result


def main():
    assert {"code": "zh", "name": "简体中文"} in LANGUAGES, "尚未注册简体中文"
    folder = ROOT / "i18n" / "translations"
    english = flatten(json.loads((folder / "en.json").read_text(encoding="utf-8")))
    chinese = flatten(json.loads((folder / "zh.json").read_text(encoding="utf-8")))
    assert english.keys() == chinese.keys(), {"missing": sorted(english.keys() - chinese.keys()), "extra": sorted(chinese.keys() - english.keys())}
    for key, value in chinese.items():
        assert isinstance(value, str) and value.strip(), f"空词条：{key}"
        assert Counter(re.findall(r"\{[^{}]+\}", value)) == Counter(re.findall(r"\{[^{}]+\}", english[key])), f"占位符不符：{key}"
    print(f"CHINESE_LANGUAGE_CHECK=PASS 词条={len(chinese)} 注册、完整性、占位符=通过")
    if "--api" not in sys.argv:
        return
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api.routers.i18n import router
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        languages = client.get("/api/i18n/languages")
        assert languages.status_code == 200
        assert {"code": "zh", "name": "简体中文"} in languages.json()["languages"]
        response = client.get("/api/i18n/zh")
        assert response.status_code == 200
        assert response.json()["ui"]["filters"]["type"] == "类型"
        assert response.json()["ui"]["buttons"]["apply"] == "应用"
    print(f"CHINESE_LANGUAGE_CHECK=PASS 词条={len(chinese)} HTTP接口=通过")


if __name__ == "__main__":
    main()
