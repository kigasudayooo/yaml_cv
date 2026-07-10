# yaml_cv: 履歴書PDF生成(Ruby+Prawn)とWord/Excel出力・Webサーバー(Python)を
# 1つのコンテナにまとめたイメージ。Podmanでのビルド・実行を想定。
#
# ビルド:  podman build -t yaml_cv:latest -f Containerfile .
# 実行:    podman run --rm -p 127.0.0.1:8000:8000 \
#            -e WEBAPP_BASIC_AUTH_USER=xxx -e WEBAPP_BASIC_AUTH_PASSWORD=yyy \
#            yaml_cv:latest

FROM docker.io/library/debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    BUNDLE_PATH=/app/vendor/bundle \
    BUNDLE_WITHOUT=documentation \
    CV_EXPORT_REPO_ROOT=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
        ruby ruby-dev bundler build-essential git \
        python3 python3-venv ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Ruby依存関係のインストール（依存ファイルのみ先にコピーしてレイヤーキャッシュを効かせる）
COPY Gemfile Gemfile.lock ./
RUN bundle install

# アプリケーション本体（uv_buildバックエンドがsrc/を要求するため先に全体をコピー）
COPY . .

# Python依存関係のインストール
RUN cd pyexport && uv sync --frozen --no-dev

RUN groupadd --system cvapp && useradd --system --gid cvapp --home-dir /app cvapp \
    && chown -R cvapp:cvapp /app
USER cvapp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD ["/app/pyexport/.venv/bin/python", "-c", \
         "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

CMD ["/app/pyexport/.venv/bin/uvicorn", "cv_export.web:app", \
     "--app-dir", "/app/pyexport/src", "--host", "0.0.0.0", "--port", "8000"]
