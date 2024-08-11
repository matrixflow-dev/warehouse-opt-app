import Vue from 'vue';
import Router from 'vue-router';
import Home from '@/components/Home';
import Features from '@/components/Features';
import Pricing from '@/components/Pricing';

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/features',
      name: 'Features',
      component: Features
    },
    {
      path: '/pricing',
      name: 'Pricing',
      component: Pricing
    }
  ]
});
