import Vue from 'vue';
import Router from 'vue-router';
import Home from '@/components/Home';
import Results from '@/components/Results';
import Inventory from '@/components/Inventory';
import PickingList from '@/components/PickingList.vue';
import PickerManagement from '@/components/PickerManagement';
import MapManagement from '@/components/MapManagement';
import APIManagement from '@/components/APIManagement';

Vue.use(Router);

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/results',
      name: 'Results',
      component: Results
    },
    {
      path: '/inventory',
      name: 'Inventory',
      component: Inventory
    },
    {
      path: '/picking-list',
      name: 'PickingList',
      component: PickingList
    },
    {
      path: '/picker-management',
      name: 'PickerManagement',
      component: PickerManagement
    },
    {
      path: '/map-management',
      name: 'MapManagement',
      component: MapManagement
    },
    {
      path: '/api-management',
      name: 'APIManagement',
      component: APIManagement
    }
  ]
});
