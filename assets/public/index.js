/**
 * This module includes code available for both the public website and
 * administration interface)
 */
//-- vendor
import Vue from 'vue';

import '@fortawesome/fontawesome-free/css/all.min.css';
import '@fortawesome/fontawesome-free/css/fontawesome.min.css';


//-- aircox
import AppBuilder from './app';
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
    appBuilder: null,
    appConfig: {},
    get app() { return this.appBuilder.app  },

    // player application
    playerBuilder: null,
    get playerApp() { return this.playerBuilder && this.playerBuilder.app },
    get player() { return this.playerApp && this.playerApp.$refs.player },

    // Handle hot-reload (link click and form submits).
    onPageFetch(event) {
        let submit = event.type == 'submit';
        let target = submit || event.target.tagName == 'A'
                        ? event.target : event.target.closest('a');
        if(!target || target.hasAttribute('target'))
            return;

        let url = submit ? target.getAttribute('action') || ''
                         : target.getAttribute('href');
        if(url===null || !(url === '' || url.startsWith('/') || url.startsWith('?')))
            return;

        let options = {};
        if(submit) {
            let formData = new FormData(event.target);
            if(target.method == 'get')
                url += '?' + (new URLSearchParams(formData)).toString();
            else {
                options['method'] = target.method;
                options['body'] = formData;
            }
        }
        this.appBuilder.fetch(url, options).then(app => {
            this.appBuilder.historySave(url);
        });
        event.preventDefault();
        event.stopPropagation();
    },

    Set: Set, Sound: Sound,
};
window.Vue = Vue;


aircox.playerBuilder = new AppBuilder({el: '#player'});
aircox.playerBuilder.load({async:true});
aircox.appBuilder = new AppBuilder(x => window.aircox.appConfig);
aircox.appBuilder.load({async:true}).then(app => {
    aircox.appBuilder.historySave(document.location, true);

    //-- load page hooks
    window.addEventListener('click', event => aircox.onPageFetch(event), true);
    window.addEventListener('submit', event => aircox.onPageFetch(event), true);
    window.addEventListener('popstate', event => {
        if(event.state && event.state.content) {
            document.title = aircox.appBuilder.title;
            aircox.appBuilder.historyLoad(event.state);
        }
    });
})


