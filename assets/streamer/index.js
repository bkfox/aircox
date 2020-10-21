import Vue from 'vue';

import {setAppConfig} from 'public/app';
import Model from 'public/model';
import Sound from 'public/sound';
import {setEcoInterval} from 'public/utils';

import {Streamer, Queue} from './controllers';

window.aircox.appConfig = {
    data() {
        return {
            // current streamer
            streamer: null,
            // all streamers
            streamers: [],
            // fetch interval id
            fetchInterval: null,

            Sound: Sound,
        }
    },

    computed: {
        apiUrl() {
            return this.$el && this.$el.dataset.apiUrl;
        },

        sources() {
            var sources = this.streamer ? this.streamer.sources : [];
            return sources.filter(s => s.data)
        },
    },

    methods: {
        fetchStreamers() {
            Streamer.Set.fetch(this.apiUrl)
                .then(streamers => {
                    Vue.set(this, 'streamers', streamers);
                    Vue.set(this, 'streamer', streamers ? streamers[0] : null);
                })
        },
    },

    mounted() {
        this.fetchStreamers();
        this.fetchInterval = setEcoInterval(() => this.streamer && this.streamer.fetch(), 5000)
    },

    destroyed() {
        if(this.fetchInterval !== null)
            clearInterval(this.fetchInterval)
    }
}

