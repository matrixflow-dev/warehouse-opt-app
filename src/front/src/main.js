import Vue from 'vue';

import './assets/custom.scss';

import { BootstrapVue, IconsPlugin } from 'bootstrap-vue';
import App from './App.vue';
import router from './router'; 
import axios from 'axios';
import VueAxios from 'vue-axios';

// Import Bootstrap and BootstrapVue CSS files (order is important)
//import 'bootstrap/dist/css/bootstrap.css';
//import 'bootstrap-vue/dist/bootstrap-vue.css';

Vue.use(BootstrapVue);
Vue.use(IconsPlugin);
Vue.use(VueAxios, axios);

Vue.config.productionTip = false;

new Vue({
  router, 
  render: h => h(App),
}).$mount('#app');