import Vue from 'vue';

import './admin.scss';

import Statistics from './statistics.vue';

Vue.component('a-statistics', Statistics)

import 'public';

window.aircox_admin = {
    /**
     * Filter items in the parent navbar-dropdown for provided key event on text input
     */
    filter_menu: function(event) {
        var filter = new RegExp(event.target.value, 'gi');
        var container = event.target.closest('.navbar-dropdown');

        if(event.target.value)
            for(var item of container.querySelectorAll('a.navbar-item'))
                item.style.display = item.innerHTML.search(filter) == -1 ? 'none' : null;
        else
            for(var item of container.querySelectorAll('a.navbar-item'))
                item.style.display = null;
    },

}




