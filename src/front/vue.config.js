const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  devServer: {
    host: '0.0.0.0',  // ホスト名
    port: 8004,       // ポート番号
    https: false,     // HTTPSプロトコルの使用
    open: true,       // 開発サーバー起動時にブラウザを自動で開くかどうか
    proxy: {
      '/api': {
        target: 'http://0.0.0.0:8000',  // FastAPIのプロキシ先
        changeOrigin: true,
        pathRewrite: { '^/api': '' },
      },
    },
  },
});
