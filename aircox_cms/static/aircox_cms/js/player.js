/*  Implementation status: -- TODO
 *  - proper design
 *  - mini-button integration in lists (list of diffusion articles)
 */


var State = Object.freeze({
    Stop: 'stop',
    Loading: 'loading',
    Play: 'play',
});


class Track {
    // Create a track with the given data.
    // If url and interval are given, use them to retrieve regularely
    // the track informations
    constructor(data) {
        Object.assign(this, data);

        if(this.data_url) {
            if(!this.interval)
                this.data_url = undefined;
            if(this.run) {
                this.run = false;
                this.start();
            }
        }
    }

    start() {
        if(this.run || !this.interval || !this.data_url)
            return;
        this.run = true;
        this.fetch_data();
    }

    stop() {
        this.run = false;
    }

    fetch_data() {
        if(!this.run || !this.interval || !this.data_url)
            return;

        var self = this;
        var req = new XMLHttpRequest();
        req.open('GET', this.data_url, true);
        req.onreadystatechange = function() {
            if(req.readyState != 4 || (req.status && req.status != 200))
                return;
            if(!req.responseText.length)
                return;

            // TODO: more consistent API
            var data = JSON.parse(req.responseText);
            if(data.type == 'track')
                data = {
                    name: '♫ ' + (data.artist ? data.artist + ' — ' : '') +
                           data.title,
                    data_url: ''
                }
            else
                data = {
                    title: data.title,
                    data_url: data.url
                }
            Object.assign(self, data);
        };
        req.send();

        if(this.run && this.interval)
            this._trigger_fetch();
    }

    _trigger_fetch() {
        if(!this.run || !this.data_url)
            return;

        var self = this;
        if(this.interval)
            window.setTimeout(function() {
                self.fetch_data();
            }, this.interval*1000);
        else
            this.fetch_data();
    }
}


/// Current selected sound (being played)
var CurrentSound = null;

var Sound = Vue.extend({
    template: '#template-sound',
    delimiters: ['[[', ']]'],

    data: function() {
        return {
            mounted: false,
            // sound state,
            state: State.Stop,
            // current position in playing sound
            position: 0,
            // url to the page related to the sound
            detail_url: '',
            // estimated position when user mouse over progress bar
            user_seek: null,
        };
    },

    computed: {
        // sound can be seeked
        seekable() {
            // seekable: for the moment only when we have a podcast file
            // note: need mounted because $refs is not reactive
            return this.mounted && this.duration && this.$refs.audio.seekable;
        },

        // sound duration in seconds
        duration() {
            return this.track.duration;
        },

        seek_position() {
            return (this.user_seek === null && this.position) ||
                    this.user_seek;
        },
    },

    props: {
        track: { type: Object, required: true },
    },

    mounted() {
        this.mounted = true;
        console.log(this.track, this.track.detail_url);
        this.detail_url = this.track.detail_url;
        this.storage_key = "sound." + this.track.sources[0];

        var pos = localStorage.getItem(this.storage_key)
        if(pos) try {
            // go back of 5 seconds
            pos = parseFloat(pos) - 5;
            if(pos > 0)
                this.$refs.audio.currentTime = pos;
        } catch (e) {}
    },

    methods: {
        //
        // Common methods
        //
        stop() {
            this.$refs.audio.pause();
            CurrentSound = null;
        },

        play(reset = false) {
            if(CurrentSound && CurrentSound != this)
                CurrentSound.stop();
            CurrentSound = this;
            if(reset)
                this.$refs.audio.currentTime = 0;
            this.$refs.audio.play();
        },

        play_stop() {
            if(this.state == State.Stop)
                this.play();
            else
                this.stop();
        },

        add_to_playlist() {
            if(!DefaultPlaylist)
                return;
            var tracks = DefaultPlaylist.tracks;
            if(tracks.indexOf(this.track) == -1)
                DefaultPlaylist.tracks.push(this.track);
        },

        remove() {
            this.stop();
            var tracks = this.$parent.tracks;
            var i = tracks.indexOf(this.track);
            if(i == -1)
                return;
            tracks.splice(i, 1);
        },

        //
        // Utils functions
        //
        _as_progress_time(event) {
            bounding = this.$refs.progress.getBoundingClientRect()
            offset = (event.clientX - bounding.left);
            return offset * this.$refs.audio.duration / bounding.width;
        },

        // format seconds into time string such as: [h"m]m'ss
        format_time(seconds) {
            seconds = Math.floor(seconds);
            var hours = Math.floor(seconds / 3600);
            seconds -= hours * 3600;
            var minutes = Math.floor(seconds / 60);
            seconds -= minutes * 60;

            return  (hours ? ((hours < 10 ? '0' + hours : hours) + '"') : '') +
                    minutes + "'" + seconds
            ;
        },


        //
        // Events
        //
        timeUpdate() {
            this.position = this.$refs.audio.currentTime;
            if(this.state == State.Play)
                localStorage.setItem(
                    this.storage_key, this.$refs.audio.currentTime
                );
        },

        ended() {
            this.state = State.Stop;
            this.$refs.audio.currentTime = 0;
            localStorage.removeItem(this.storage_key);
            this.$emit('ended', this);
        },

        progress_mouse_out(event) {
            this.user_seek = null;
        },

        progress_mouse_move(event) {
            if(this.$refs.audio.duration == Infinity ||
                    isNaN(this.$refs.audio.duration))
               return;
            this.user_seek = this._as_progress_time(event);
        },

        progress_clicked(event) {
            this.$refs.audio.currentTime = this._as_progress_time(event);
            this.play();
            event.stopImmediatePropagation();
        },
    }
});


/// User's default playlist
DefaultPlaylist = null;

var Playlist = Vue.extend({
    template: '#template-playlist',
    delimiters: ['[[', ']]'],
    data() {
        return {
            // if true, use this playlist as user's default playlist
            default: false,
            // read all mode enabled
            read_all: false,
            // playlist can be modified by user
            modifiable: false,
            // if set, save items into localstorage using this root key
            storage_key: null,
            // sounds info
            tracks: [],
        };
    },

    computed: {
        // id of the read all mode checkbox switch
        read_all_id() {
            return this.id + "_read_all";
        }
    },

    mounted() {
        // set default
        if(this.default) {
            if(DefaultPlaylist)
                this.tracks = DefaultPlaylist.tracks;
            else
                DefaultPlaylist = this;
        }

        // storage_key
        if(this.storage_key) {
            tracks = localStorage.getItem('playlist.' + this.storage_key);
            if(tracks)
                this.tracks = JSON.parse(tracks);
        }
    },

    methods: {
        sound_ended(sound) {
            // ensure sound is stopped (beforeDestroy())
            sound.stop();

            // next only when read all mode
            if(!this.read_all)
                return;

            var sounds = this.$refs.sounds;
            var id = sounds.findIndex(s => s == sound);
            if(id < 0 || id+1 >= sounds.length)
                return
            id++;
            sounds[id].play(true);
        },
    },

    watch: {
        tracks: {
            handler() {
                if(!this.storage_key)
                    return;
                localStorage.setItem('playlist.' + this.storage_key,
                                     JSON.stringify(this.tracks));
            },
            deep: true,
        }
    }
});

Vue.component('a-sound', Sound);
Vue.component('a-playlist', Playlist);

