import Vue from 'vue';

import Player from './player.vue';
import Tab from './tab.vue';
import Tabs from './tabs.vue';

Vue.component('a-player', Player);
Vue.component('a-tab', Tab);
Vue.component('a-tabs', Tabs);

export {Player, Tab, Tabs};


