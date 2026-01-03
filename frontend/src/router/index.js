import Vue from 'vue';
import Router from 'vue-router';

import Dashboard from '@/views/Dashboard.vue';
import EdgeDetail from '@/views/EdgeDetail.vue';
import LogsAudit from '@/views/LogsAudit.vue';
import Governance from '@/views/Governance.vue';

Vue.use(Router);

export default new Router({
  mode: 'history',
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/edge/:addr', name: 'edgeDetail', component: EdgeDetail },
    { path: '/audit', name: 'audit', component: LogsAudit },
    { path: '/governance', name: 'governance', component: Governance },
  ],
});
