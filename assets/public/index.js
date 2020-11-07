/**
 * This module includes code available for both the public website and
 * administration interface)
 */
//-- vendor
import Vue from 'vue';

import '@fortawesome/fontawesome-free/css/all.min.css';
import '@fortawesome/fontawesome-free/css/fontawesome.min.css';


//-- aircox
import App from './app';
import Sound from './sound';
import {Set} from './model';

import './styles.scss';

import Autocomplete from './autocomplete';
import Episode from './episode';
import Player from './player';
import Playlist from './playlist';
import SoundItem from './soundItem';

Vue.component('a-autocomplete', Autocomplete)
Vue.component('a-episode', Episode)
Vue.component('a-player', Player)
Vue.component('a-playlist', Playlist)
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
    },

    loadPage(url) {
        fetch(url).then(response => response.text())
            .then(response => {
                let doc = new DOMParser().parseFromString(response, 'text/html');

                aircox.app && aircox.app.$destroy();
                document.getElementById('app').innerHTML = doc.getElementById('app').innerHTML;
                App(() => window.aircox.appConfig, true).then(app => {
                    aircox.app = app;
                    document.title = doc.title;
                })
            });
    },

    Set: Set, Sound: Sound,
};
window.Vue = Vue;


App({el: '#player'}).then(app => window.aircox.playerApp = app);
App(() => window.aircox.appConfig).then(app => {
    window.aircox.app = app;
    window.addEventListener('click', event => {
        let target = event.target.tagName == 'A' ? event.target : event.target.closest('a');
        if(!target || !target.hasAttribute('href'))
            return;

        let href = target.getAttribute('href');
        if(href && href !='#') {
            window.aircox.loadPage(href);
            event.preventDefault();
            event.stopPropagation();
        }
    }, true);
})


