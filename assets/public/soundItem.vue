<template>
    <div class="media">
        <div class="media-left" v-if="hasAction('play')">
            <button class="button" @click="$emit('togglePlay')">
                <div class="icon">
                    <span class="fa fa-pause" v-if="playing || loading"></span>
                    <span class="fa fa-play" v-else></span>
                </div>
            </button>
        </div>
        <div class="media-content">
            <slot name="content" :player="player" :item="item" :loaded="loaded">
                <h4 class="title is-4 is-inline-block">
                    {{ name || item.name }}
                </h4>
            </slot>
        </div>
        <div class="media-right">
            <button class="button" v-if="player.$refs.pin != $parent" @click.stop="player.togglePin(item)">
                <span class="icon is-small">
                    <span :class="(pinned ? '' : 'has-text-grey-light ') + 'fa fa-thumbtack'"></span>
                </span>
            </button>
            <slot name="actions" :player="player" :item="item" :loaded="loaded"></slot>
        </div>
    </div>
</template>
<script>
import Model from './model';
import Sound from './sound';

export default {
    props: {
        data: {type: Object, default: x => {}},
        name: String,
        cover: String,
        player: Object,
        page_url: String,
        actions: {type:Array, default: x => []},
        index: {type:Number, default: null},
    },

    computed: {
        item() { return this.data instanceof Model ? this.data : new Sound(this.data || {}); },
        loaded() { return this.player && this.player.isLoaded(this.item) },
        playing() { return this.player && this.player.playing && this.loaded },
        paused()  { return this.player && this.player.paused && this.loaded },
        loading() { return this.player && this.player.loading && this.loaded },
        pinned() { return this.player && this.player.sets.pin.find(this.item) },
    },

    methods: {
        hasAction(action) {
            return this.actions && this.actions.indexOf(action) != -1;
        },
    }
}
</script>
