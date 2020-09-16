<template>
    <div class="media">
        <div class="media-left">
            <div class="button" @click="toggle()"
                    :title="buttonTitle" :aria-label="buttonTitle">
                <span class="fas fa-pause" v-if="playing"></span>
                <span class="fas fa-play" v-else></span>
            </div>
            <audio ref="audio" @playing="onChange" @ended="onChange" @pause="onChange">
                <slot name="sources"></slot>
            </audio>
        </div>
        <div class="media-left media-cover" v-if="onAir && onAir.cover">
            <img :src="onAir.cover" class="cover" />
        </div>
        <div class="media-content" v-if="onAir && onAir.type == 'track'">
            <slot name="track" :onAir="onAir" :liveInfo="liveInfo"></slot>
        </div>
        <div class="media-content" v-else-if="onAir && onAir.type == 'diffusion'">
            <slot name="diffusion" :onAir="onAir" :liveInfo="liveInfo"></slot>
        </div>
        <div class="media-content" v-else><slot name="empty"></slot></div>
        </div>
    </div>
</template>


<script>
import LiveInfo from './liveInfo';

export const State = {
    paused: 0,
    playing: 1,
    loading: 2,
}

export default {
    data() {
        return {
            state: State.paused,
            liveInfo: this.liveInfoUrl ? new LiveInfo(this.liveInfoUrl, this.liveInfoTimeout)
                                       : null,
        }
    },

    props: {
        buttonTitle: String,
        liveInfoUrl: String,
        liveInfoTimeout: { type: Number, default: 5},
        src: String,
    },

    computed: {
        paused() { return this.state == State.paused; },
        playing() { return this.state == State.playing; },
        loading() { return this.state == State.loading; },

        onAir() {
            return this.liveInfo && this.liveInfo.items && this.liveInfo.items[0];
        },

        buttonStyle() {
            if(!this.onAir)
                return;
            return { backgroundImage: `url(${this.onAir.cover})` }
        }
    },

    methods: {
        load(src) {
            const audio = this.$refs.audio;
            audio.src = src;
            audio.load()
        },

        play(src) {
            if(src)
                this.load(src);
            this.$refs.audio.play().catch(e => console.error(e))
        },

        pause() {
            this.$refs.audio.pause()
        },

        toggle() {
            if(this.paused)
                this.play()
            else
                this.pause()
        },

        onChange(event) {
            const audio = this.$refs.audio;
            this.state = audio.paused ? State.paused : State.playing;
        },
    },

    mounted() {
        this.liveInfo && this.liveInfo.refresh()
    },

    destroyed() {
        this.liveInfo && this.liveInfo.drop()
    },
}

</script>




