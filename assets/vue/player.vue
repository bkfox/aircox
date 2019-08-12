<template>
    <div class="media">
        <div class="media-left">
            <div class="button is-size-4" @click="toggle()">
                <span class="fas fa-pause" v-if="playing"></span>
                <span class="fas fa-play" v-else></span>
            </div>
            <audio ref="audio" @playing="onChange" @ended="onChange" @pause="onChange">
                <slot name="sources"></slot>
            </audio>
        </div>
        <div class="media-content">
        </div>
    </div>
</template>


<script>
export const State = {
    paused: 0,
    playing: 1,
    loading: 2,
}

export default {
    data() {
        return {
            state: State.paused,
        }
    },

    props: {
        onAir: String,
        src: String,
    },

    computed: {
        paused() { return this.state == State.paused; },
        playing() { return this.state == State.playing; },
        loading() { return this.state == State.loading; },
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
        this.load(this.src);
    }
}

</script>




