<template>
    <div>
        <slot name="header"></slot>
        <ul :class="listClass">
            <li v-for="(item,index) in items" :class="itemClass" @click="!hasAction('play') && select(index)">
                <a :class="index == selectedIndex ? 'is-active' : ''">
                    <SoundItem
                        :data="item" :index="index" :player="player" :set="set"
                        @togglePlay="togglePlay(index)"
                        :actions="actions">
                        <template v-slot:actions="{loaded,set}">
                            <button class="button" v-if="editable" @click.stop="remove(index,true)">
                                <span class="icon is-small"><span class="fa fa-minus"></span></span>
                            </button>
                        </template>
                    </SoundItem>
                </a>
            </li>
        </ul>
        <slot name="footer"></slot>
    </div>
</template>
<script>
import List from './list';
import SoundItem from './soundItem';

export default {
    extends: List,

    props: {
        actions: Array,
        name: String,
        player: Object,
        editable: Boolean,
    },

    computed: {
        self() { return this; }
    },

    methods: {
        hasAction(action) { return this.actions && this.actions.indexOf(action) != -1; },

        selectNext() {
            let index = this.selectedIndex + 1;
            return this.select(index >= this.items.length ? -1 : index);
        },

        togglePlay(index) {
            if(this.player.isPlaying(this.set.get(index)))
                this.player.pause();
            else
                this.select(index)
        },
    },
    components: { List, SoundItem },
}
</script>
