<template>
    <div class="media sound-item">
        <div class="media-left">
            <img class="cover is-tiny" :src="item.data.cover" v-if="item.data.cover">
        </div>
        <div class="media-left">
            <button class="button" @click.stop="$emit('togglePlay')">
                <div class="icon">
                    <span class="fa fa-pause" v-if="playing"></span>
                    <span class="fa fa-play" v-else></span>
                </div>
            </button>
        </div>
        <div class="media-content">
            <slot name="content" :player="player" :item="item" :loaded="loaded">
                <h4 class="title is-4">{{ name || item.name }}</h4>
                <a class="subtitle is-6 is-inline-block" v-if="hasAction('page') && item.data.page_url"
                    :href="item.data.page_url">
                    {{ item.data.page_title }}
                </a>
            </slot>
        </div>
        <div class="media-right">
            <button class="button" v-if="player.sets.pin != $parent.set" @click.stop="player.togglePin(item)">
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
        player: Object,
        page_url: String,
        actions: {type:Array, default: x => []},
        index: {type:Number, default: null},
    },

    computed: {
        item() { return this.data instanceof Model ? this.data : new Sound(this.data || {}); },
        loaded() { return this.player && this.player.isLoaded(this.item) },
        playing() { return this.player && this.player.isPlaying(this.item) },
        paused()  { return this.player && this.player.paused && this.loaded },
        pinned() { return this.player && this.player.sets.pin.find(this.item) },
    },

    methods: {
        hasAction(action) {
            return this.actions && this.actions.indexOf(action) != -1;
        },
    }
}
</script>
