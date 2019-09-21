/**
 * This module includes code available for both the public website and
 * administration interface)
 */
//-- vendor
import Vue from 'vue';

import '@fortawesome/fontawesome-free/css/all.min.css';
import '@fortawesome/fontawesome-free/css/fontawesome.min.css';


//-- aircox
import {appConfig, loadApp} from './app';

import './styles.scss';

import Player from './player.vue';
import Autocomplete from './autocomplete.vue';

Vue.component('a-player', Player)
Vue.component('a-autocomplete', Autocomplete)


window.aircox = {
    // main application
    app: null,

    // main application config
    appConfig: {},

    // player application
    playerApp: null,

    // player component
    get player() {
        return this.playerApp && this.playerApp.$refs.player
    }
};


loadApp({el: '#player'}).then(app => { window.aircox.playerApp = app },
                              () => undefined)
loadApp(() => window.aircox.appConfig ).then(app => { window.aircox.app = app },
                                             () => undefined)


