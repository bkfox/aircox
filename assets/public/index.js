/**
 * This module includes code available for both the public website and
 * administration interface)
 */
//-- vendor
import Vue from 'vue';

import '@fortawesome/fontawesome-free/css/all.min.css';
import '@fortawesome/fontawesome-free/css/fontawesome.min.css';
import 'buefy/dist/buefy.css';


//-- aircox
import app from './app';
import LiveInfo from './liveInfo';

import './styles.scss';

import Player from './player.vue';

Vue.component('a-player', Player)


window.aircox = {
    app: app,
    LiveInfo: LiveInfo,
}

