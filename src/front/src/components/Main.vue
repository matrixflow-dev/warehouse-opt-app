<template>
  <b-navbar toggleable="lg" type="dark" variant="primary">
    <b-navbar-brand class="brand" href="#">倉庫管理AI</b-navbar-brand>
    <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
    <b-collapse id="nav-collapse" is-nav>
      <b-navbar-nav>
        <b-nav-item tag="router-link" to="/">ホーム</b-nav-item>
        <b-nav-item tag="router-link" to="/features">結果</b-nav-item>
        <b-nav-item tag="router-link" to="/features">在庫情報</b-nav-item>
        <b-nav-item tag="router-link" to="/features">ピッカー管理</b-nav-item>
        <b-nav-item tag="router-link" to="/pricing">マップ管理</b-nav-item>
        <b-nav-item tag="router-link" to="/pricing">API管理</b-nav-item>
      </b-navbar-nav>
      <b-navbar-nav class="ml-auto">
      </b-navbar-nav>
    </b-collapse>
  </b-navbar>
</template>

<script>
export default {
  name: 'Main',
  data() {
    return {
    }
  }
}
</script>

<style scoped>
.brand {
  padding-left: 30px;
}
</style>