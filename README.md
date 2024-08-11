# Warehouse Optimization App (倉庫管理 AI のアプリケーション)

## 概要

Warehouse Optimization App は、倉庫の効率を最大化するための AI を活用したアプリケーションです。
SIP で構築したアルゴリズムをウェブアプリケーション化したもの

## 特徴

- **出荷の迅速化**: AI が最適な出荷順序を提案し、出荷業務を効率化します。

## システム要件

- Docker
- シェルスクリプトを実行できる環境 (Linux, macOS, または WSL)

## ビルド方法

このアプリケーションをビルドするには、以下の手順に従ってください。

1. リポジトリをクローンします。

   ```sh
   git clone https://github.com/your-repo/warehouse-opt-app.git
   cd warehouse-opt-app
   ```

2. `build.sh`スクリプトを実行してアプリケーションをビルドします。

   ```sh
   cd src/
   ./build.sh
   ```

## 起動方法

ビルドが完了したら、以下のコマンドでアプリケーションを起動できます。

```sh
docker run -p 80:80 --rm -it behavior_opt_local
```

このコマンドは、Docker コンテナ内でアプリケーションを実行し、ホストマシンのポート 80 でサービスを提供します。

## 使用例

アプリケーションにアクセスするには、ウェブブラウザを開き、以下の URL にアクセスします。

```
http://localhost
```

ここで、AI を利用した倉庫管理機能を試すことができます。
