<template>
    <a :class="[active ? activeClass : '']" @click="actions.indexOf('play') == -1 && play()">
        <div class="media">
            <div class="media-left" v-if="hasAction('play')">
                <button class="button" @click="play()">
                    <div class="icon">
                        <span class="fa fa-pause" v-if="playing || loading"></span>
                        <span class="fa fa-play" v-else></span>
                    </div>
                </button>
            </div>
            <div class="media-content">
                <slot name="content" :player="player" :item="item" :active="active">
                    <h4 class="title is-4 is-inline-block">
                        {{ name || item.name }}
                    </h4>
                </slot>
            </div>
            <div class="media-right">
                <button class="button" v-if="hasAction('queue')" @click.stop="player.push(item)">
                    <span class="icon is-small"><span class="fa fa-list"></span></span>
                </button>
                <button class="button" v-if="hasAction('remove')" @click.stop="set.remove(item)">
                    <span class="icon is-small"><span class="fa fa-minus"></span></span>
                </button>
                <slot name="actions" :player="player" :item="item" :active="active"></slot>
            </div>
        </div>
    </a>
</template>
<script>
import Model from './model';
import Sound from './sound';

export default {
    props: {
        data: {type: Object, default: x => {}},
        name: String,
        cover: String,
        set: Object,
        player: Object,
        page_url: String,
        activeClass: String,
        actions: {type:Array, default: x => []},
    },

    computed: {
        item() { return this.data instanceof Model ? this.data : new Sound(this.data || {}); },
        active() { return this.player && this.player.isActive(this.item) },
        playing() { return this.player && this.player.playing && this.active },
        paused()  { return this.player && this.player.paused && this.active },
        loading() { return this.player && this.player.loading && this.active },
    },

    methods: {
        hasAction(action) {
            return this.actions && this.actions.indexOf(action) != -1;
        },

        play() {
            if(this.player && this.active)
                this.player.togglePlay()
            else
                this.player.play(this.item);
        },

        push_to(playlist) {
            this.player.playlists[playlist].push(this.item, {unique_key:'id'});
        },
    }
}
</script>
