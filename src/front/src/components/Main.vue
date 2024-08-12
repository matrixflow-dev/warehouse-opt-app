<template>
  <b-navbar toggleable="lg" type="dark" variant="primary">
    <b-navbar-brand class="brand" href="#">倉庫管理AI</b-navbar-brand>
    <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
    <b-collapse id="nav-collapse" is-nav>
      <b-navbar-nav>
        <b-nav-item tag="router-link" to="/">ホーム</b-nav-item>
        <b-nav-item tag="router-link" to="/results">結果</b-nav-item>
        <b-nav-item tag="router-link" to="/inventory">在庫情報</b-nav-item>
        <b-nav-item tag="router-link" to="/picking-list">ピッキングリスト</b-nav-item>
        <b-nav-item tag="router-link" to="/picker-management">ピッカー管理</b-nav-item>
        <b-nav-item tag="router-link" to="/map-management">マップ管理</b-nav-item>
        <b-nav-item tag="router-link" to="/api-management">API管理</b-nav-item>
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