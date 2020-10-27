<template>
    <div class="player">
        <Playlist ref="history" class="panel-menu menu" v-show="panel == 'history'"
            name="History"
            :editable="true" :player="self" :set="sets.history" @select="play('pin', $event.index)"
            listClass="menu-list" itemClass="menu-item">
            <template v-slot:header="">
                <p class="menu-label">
                    <span class="icon"><span class="fa fa-clock"></span></span>
                    History
                </p>
            </template>
        </Playlist>
        <Playlist ref="pin" class="player-panel menu" v-show="panel == 'pin'"
            name="Pinned"
            :editable="true" :player="self" :set="sets.pin" @select="play('pin', $event.index)" 
            listClass="menu-list" itemClass="menu-item">
            <template v-slot:header="">
                <p class="menu-label">
                    <span class="icon"><span class="fa fa-thumbtack"></span></span>
                    Pinned
                </p>
            </template>
        </Playlist>
        <Playlist ref="queue" class="player-panel menu" v-show="panel == 'queue'"
            :editable="true" :player="self" :set="sets.queue" @select="play('queue', $event.index)" 
            listClass="menu-list" itemClass="menu-item">
            <template v-slot:header="">
                <p class="menu-label">
                    <span class="icon"><span class="fa fa-list"></span></span>
                    Playlist
                </p>
            </template>
        </Playlist>

        <div class="player-bar media">
            <div class="media-left">
                <div class="button" @click="togglePlay()"
                        :title="buttonTitle" :aria-label="buttonTitle">
                    <span class="fas fa-pause" v-if="playing"></span>
                    <span class="fas fa-play" v-else></span>
                </div>
                <audio ref="audio" preload="metadata"
                    @playing="onState" @ended="onState" @pause="onState">
                </audio>
                <slot name="sources"></slot>
            </div>
            <div class="media-left media-cover" v-if="current && current.cover">
                <img :src="current.cover" class="cover" />
            </div>
            <div class="media-content">
                <slot name="content" :current="current"></slot>
            </div>
            <div class="media-right">
                <button class="button has-text-weight-bold" v-if="loaded" @click="playLive()">
                    <span class="icon has-text-danger">
                        <span class="fa fa-broadcast-tower"></span>
                    </span>
                    <span>Live</span>
                </button>
                <button :class="playlistButtonClass('history')"
                        @click="togglePanel('history')">
                    <span class="mr-2 is-size-6" v-if="sets.history.length">
                        {{ sets.history.length }}</span>
                    <span class="icon"><span class="fa fa-clock"></span></span>
                </button>
                <button :class="playlistButtonClass('pin')"
                        @click="togglePanel('pin')">
                    <span class="mr-2 is-size-6" v-if="sets.pin.length">
                        {{ sets.pin.length }}</span>
                    <span class="icon"><span class="fa fa-thumbtack"></span></span>
                </button>
                <button :class="playlistButtonClass('queue')"
                        @click="togglePanel('queue')">
                    <span class="mr-2 is-size-6" v-if="sets.queue.length">
                        {{ sets.queue.length }}</span>
                    <span class="icon"><span class="fa fa-list"></span></span>
                </button>

            </div>
        </div>
        <div v-if="progress">
            <span :style="{ width: progress }"></span>
        </div>
    </div>
</template>

<script>
import Vue, { ref } from 'vue';
import Live from './live';
import Playlist from './playlist';
import Sound from './sound';
import {Set} from './model';


export const State = {
    paused: 0,
    playing: 1,
    loading: 2,
}

export default {
    data() {
        return {
            state: State.paused,
            /// Loaded item
            loaded: null,
            /// Live instance
            live: this.liveArgs ? new Live(this.liveArgs) : null,
            //! Active panel name
            panel: null,
            //! current playing playlist component
            playlist: null,
            //! players' playlists' sets
            sets: {
                queue: Set.storeLoad(Sound, "playlist.queue", { max: 30, unique: true }),
                pin: Set.storeLoad(Sound, "player.pin", { max: 30, unique: true }),
                history: Set.storeLoad(Sound, "player.history", { max: 30, unique: true }),
            }
        }
    },

    props: {
        buttonTitle: String,
        liveArgs: Object,
    },

    computed: {
        paused() { return this.state == State.paused; },
        playing() { return this.state == State.playing; },
        loading() { return this.state == State.loading; },
        self() { return this; },

        current() {
            return this.loaded || this.live && this.live.current;
        },

        progress() {
            let audio = this.$refs.audio;
            return audio && Number.isFinite(audio.duration) && audio.duration ?
                audio.pos / audio.duration * 100 : null;
        },

        buttonStyle() {
            if(!this.current)
                return;
            return { backgroundImage: `url(${this.current.cover})` }
        },
    },

    methods: {
        playlistButtonClass(name) {
            let set = this.sets[name];
            return (set ? (set.length ? "" : "has-text-grey-light ")
                       + (this.panel == name ? "is-info "
                          : this.playlist && this.playlist == this.$refs[name] ? 'is-primary '
                          : '') : '')
                + "button has-text-weight-bold";
        },

        /// Show/hide panel
        togglePanel(panel) {
            this.panel = this.panel == panel ? null : panel;
        },

        /// Return True if item is loaded
        isLoaded(item) {
            return this.loaded && this.loaded.src == item.src;
        },

        /// Return True if item is loaded
        isPlaying(item) {
            return this.isLoaded(item) && !this.player.paused;
        },

        load(playlist, {src=null, item=null}={}) {
            src = src || item.src;
            this.loaded = item;
            this.playlist = playlist ? this.$refs[playlist] : null;

            const audio = this.$refs.audio;
            if(src instanceof Array) {
                audio.innerHTML = '';
                for(var s of src) {
                    let source = document.createElement(source);
                    source.setAttribute('src', s);
                    audio.appendChild(source)
                }
            }
            else {
                audio.src = src;
            }
            audio.load();
        },

        /// Play a playlist's sound (by playlist name, and sound index)
        play(playlist=null, index=0) {
            if(!playlist)
                playlist = 'queue';

            let item = this.$refs[playlist].get(index);
            if(item) {
                this.load(playlist, {item: item});
                this.sets.history.push(item);
                this.$refs.audio.play().catch(e => console.error(e))
            }
            else
                throw `No sound at index ${index} for playlist ${playlist}`;
        },

        /// Push items to playlist (by name)
        push(playlist, ...items) {
            this.$refs[playlist].push(...items);
        },

        /// Push and play items
        playItems(playlist, ...items) {
            this.push(playlist, ...items);

            let index = this.$refs[playlist].findIndex(items[0]);
            this.$refs[playlist].selectedIndex = index;
            this.play(playlist, index);
        },

        /// Play live stream
        playLive() {
            this.load(null, {src: this.live.src});
            this.$refs.audio.play().catch(e => console.error(e))
            this.panel = '';
        },

        /// Pause
        pause() {
            this.$refs.audio.pause()
        },

        //! Play/pause
        togglePlay() {
            if(this.paused)
                this.$refs.audio.play().catch(e => console.error(e))
            else
                this.pause()
        },

        //! Pin/Unpin an item
        togglePin(item) {
            let index = this.sets.pin.findIndex(item);
            if(index > -1)
                this.sets.pin.remove(index);
            else {
                this.sets.pin.push(item);
                if(!this.panel)
                    this.panel = 'pin';
            }
        },

        /// Audio player state change event
        onState(event) {
            const audio = this.$refs.audio;
            this.state = audio.paused ? State.paused : State.playing;

            if(event.type == 'ended' && (!this.playlist || this.playlist.selectNext() == -1))
                this.playLive();
        },
    },

    mounted() {
        this.sources = this.$slots.sources;
    },

    components: { Playlist },
}
</script>


