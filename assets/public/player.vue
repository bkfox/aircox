<template>
    <div class="player">
        <List ref="queue" class="player-panel menu" v-show="panel == 'queue' && queue.length"
            :set="queue" @select="onSelect" 
            listClass="menu-list" itemClass="menu-item">
            <template v-slot:header>
                <p class="menu-label">
                    <span class="icon"><span class="fa fa-list"></span></span>
                    Playlist
                </p>
            </template>
            <template v-slot:item="{item,index,set}">
                <SoundItem activeClass="is-active" :data="item" :player="self" :set="set"
                    :actions="['remove']">
                    <template v-slot:actions="{active,set}">
                        <!-- TODO: stop player if active -->

                    </template>
                </SoundItem>
            </template>
        </List>
        <List ref="history" class="player-panel menu" v-show="panel == 'history' && history.length"
            :set="history" @select="onSelect"
            listClass="menu-list" itemClass="menu-item">
            <template v-slot:header>
                <p class="menu-label">
                    <span class="icon"><span class="fa fa-clock"></span></span>
                    History
                </p>
            </template>
            <template v-slot:item="{item,index,set}">
                <SoundItem activeClass="is-active" :data="item" :player="self" :set="set"
                    :actions="['queue','remove']">
                </SoundItem>
            </template>
        </List>
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
                <button class="button" v-if="active" @click="load() && play()">
                    <span class="icon has-text-danger">
                        <span class="fa fa-broadcast-tower"></span>
                    </span>
                    <span>Live</span>
                </button>

                <button class="button" v-if="history.length"
                    @click="togglePanel('history')"
                    :class="[panel == 'history' ? 'is-info' : '']" >
                    <span class="icon">
                        <span class="fa fa-clock"></span>
                    </span>
                </button>
                <button class="button" v-if="queue.length"
                    @click="togglePanel('queue')"
                    :class="[panel == 'queue' ? 'is-info' : '']" >
                    <span class="mr-2 is-size-6">{{ queue.length }}</span>
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
import List from './list';
import SoundItem from './soundItem';
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
            active: null,
            live: this.liveArgs ? new Live(this.liveArgs) : null,
            panel: null,
            queue: Set.storeLoad(Sound, "player.queue", { max: 30, unique: true }),
            history: Set.storeLoad(Sound, "player.history", { max: 30, unique: true }),
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
            return this.active || this.live && this.live.current;
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
        togglePanel(panel) {
            this.panel = this.panel == panel ? null : panel;
        },

        isActive(item) {
            return item && this.active && this.active.src == item.src;
        },

        _load(src) {
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

        load(item) {
            if(item) {
                this._load(item.src)
                this.history.push(item);
            }
            else
                this._load(this.live.src);
            this.$set(this, 'active', item);
        },

        play(item) {
            if(item)
                this.load(item);
            this.$refs.audio.play().catch(e => console.error(e))
        },

        pause() {
            this.$refs.audio.pause()
        },

        //! Play/pause
        togglePlay() {
            if(this.paused)
                this.play()
            else
                this.pause()
        },

        //! Push item to queue
        push(item) {
            this.queue.push(item);
            this.panel = 'queue';
        },

        onState(event) {
            const audio = this.$refs.audio;
            this.state = audio.paused ? State.paused : State.playing;

            if(event.type == 'ended' && this.active) {
                this.queue.remove(this.active);
                if(this.queue.length)
                    this.$refs.queue.select(0);
                else
                    this.load();
            }
        },

        onSelect({item,index}) {
            if(!this.isActive(item))
                this.play(item);
        },
    },

    mounted() {
        this.sources = this.$slots.sources;
    },

    components: {
        List, SoundItem,
    },
}
</script>


