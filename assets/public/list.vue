<template>
    <div>
        <slot name="header"></slot>
        <ul :class="listClass">
            <slot name="start"></slot>
            <template v-for="(item,index) in items">
                <li :class="itemClass" @click="select(index)">
                    <slot name="item" :set="set" :index="index" :item="item"></slot>
                </li>
            </template>
            <slot name="end"></slot>
        </ul>
        <slot name="footer"></slot>
    </div>
</template>
<script>
export default {
    data() {
        return {
            selectedIndex: this.default,
        }
    },

    props: {
        listClass: String,
        itemClass: String,
        default: { type: Number, default: -1},
        set: Object,
    },

    computed: {
        model() { return this.set.model },
        items() { return this.set.items },
        length() { return this.set.length },

        selected() {
            return this.items && this.items.length > this.selectedIndex > -1
                ? this.items[this.selectedIndex] : null;
        },
    },

    methods: {
        select(index=null) {
            if(index === null)
                index = this.selectedIndex;
            else if(this.selectedIndex == index)
                return;

            this.selectedIndex = Math.min(index, this.items.length-1);
            this.$emit('select', { item: this.selected, index: this.selectedIndex });
            return this.selectedIndex;
        },

        selectNext() {
            let index = this.selectedIndex + 1;
            return this.select(index >= this.items.length ? -1 : index);
        },

        // add()
        // insert() + drag & drop
        // remove()
    },
}
</script>
