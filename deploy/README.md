# Linuxサーバーへのデプロイ（Podman + systemd）

`yaml_cv` を Web サービスとして常時起動するための手順。Podman の
[Quadlet](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
を使い、systemd がコンテナのライフサイクル（起動・再起動・ヘルスチェック連動）を管理する。

## 前提

* サーバー: Linux（systemd必須）、Podman 4.4以上（Quadlet対応）
* rootlessユーザーで運用する想定（`loginctl enable-linger <user>` でユーザーsystemdをブート時から有効化しておく）
* 外部公開はリバースプロキシ（nginx / Caddy 等）経由。このコンテナ自体は
  `127.0.0.1:8000` にのみバインドし、TLS終端や外部向けポートは持たない設計。

## 手順

### 1. リポジトリ取得とイメージビルド

```sh
git clone https://github.com/<your-account>/yaml_cv.git
cd yaml_cv
podman build -t yaml_cv:latest -f Containerfile .
```

サーバー上に直接cloneしてビルドする方法を基本とする。CI等でイメージを配布したい場合は
コンテナレジストリ（ghcr.io等）へpushし、`deploy/yaml-cv.container` の `Image=` を書き換える。

### 2. Basic認証情報の設定

```sh
mkdir -p ~/.config/yaml_cv
cp deploy/web.env.example ~/.config/yaml_cv/web.env
chmod 600 ~/.config/yaml_cv/web.env
$EDITOR ~/.config/yaml_cv/web.env   # WEBAPP_BASIC_AUTH_USER / PASSWORD を必ず変更
```

**`WEBAPP_BASIC_AUTH_USER`/`WEBAPP_BASIC_AUTH_PASSWORD` を設定しない場合、
アプリケーションは認証なしで動作する。** インターネットに公開する前に必ず設定すること。

### 3. Quadletユニットの配置

```sh
mkdir -p ~/.config/containers/systemd
cp deploy/yaml-cv.container ~/.config/containers/systemd/
systemctl --user daemon-reload
systemctl --user enable --now yaml-cv.service
```

### 4. 動作確認

```sh
systemctl --user status yaml-cv.service
curl http://127.0.0.1:8000/healthz
```

### 5. リバースプロキシ設定（例: Caddy）

```
cv.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

TLS終端はCaddy/nginx側に任せる。Basic認証はアプリ側で行っているため、
プロキシ側で重ねて認証をかける必要はない（かけても構わない）。

## 更新方法

```sh
cd yaml_cv
git pull
podman build -t yaml_cv:latest -f Containerfile .
systemctl --user restart yaml-cv.service
```

## アンインストール

```sh
systemctl --user disable --now yaml-cv.service
rm ~/.config/containers/systemd/yaml-cv.container
podman rmi yaml_cv:latest
```
