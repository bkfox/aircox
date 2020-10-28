<template>
    <div>
        <slot name="header"></slot>
        <ul :class="listClass">
            <template v-for="(item,index) in items">
                <li :class="itemClass" @click="select(index)">
                    <slot name="item" :selected="index == selectedIndex" :set="set" :index="index" :item="item"></slot>
                </li>
            </template>
        </ul>
        <slot name="footer"></slot>
    </div>
</template>
<script>
export default {
    data() {
        return {
            selectedIndex: this.defaultIndex,
        }
    },

    props: {
        listClass: String,
        itemClass: String,
        defaultIndex: { type: Number, default: -1},
        set: Object,
    },

    computed: {
        model() { return this.set.model },
        items() { return this.set.items },
        length() { return this.set.length },

        selected() {
            return this.selectedIndex > -1 && this.items.length > this.selectedIndex > -1
                ? this.items[this.selectedIndex] : null;
        },
    },

    methods: {
        get(index) { return this.set.get(index) },
        find(item) { return this.set.find(item) },
        findIndex(item) { return this.set.findIndex(item) },

        push(...items) {
            let index = this.set.length;
            for(var item of items)
                this.set.push(item);
        },

        remove(index, select=False) {
            this.set.remove(index);
            if(index < this.selectedIndex)
                this.selectedIndex--;
            if(select && this.selectedIndex == index)
                this.select(index)
        },

        select(index) {
            this.selectedIndex = index > -1  && this.items.length ? index % this.items.length : -1;
            this.$emit('select', { item: this.selected, index: this.selectedIndex });
            return this.selectedIndex;
        },


    },
}
</script>
