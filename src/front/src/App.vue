<template>
  <div>
    <Main />
    <router-view class="content-view" />
  </div>
</template>

<script>
import Main from './components/Main.vue'

export default {
  name: 'App',
  components: {
    Main
  }
}
</script>

<style>
.content-view {
  margin: 20px;
  padding: 20px;
}
</style>
