/**
 * This module includes code available for both the public website and
 * administration interface)
 */
//-- vendor
import Vue from 'vue';

import '@fortawesome/fontawesome-free/css/all.min.css';
import '@fortawesome/fontawesome-free/css/fontawesome.min.css';


//-- aircox
import {App} from './app';

import './styles.scss';

import Autocomplete from './autocomplete.vue';
import Player from './player.vue';
import SoundItem from './soundItem';

Vue.component('a-autocomplete', Autocomplete)
Vue.component('a-player', Player)
Vue.component('a-sound-item', SoundItem)


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


App({el: '#player'}).then(app => window.aircox.playerApp = app,
                          () => undefined);
App(() => window.aircox.appConfig).then(app => { window.aircox.app = app },
                                        () => undefined)


