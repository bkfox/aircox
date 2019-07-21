<template>
    <div>
        <div class="tabs is-centered">
            <ul><slot name="tabs" :value="value" /></ul>
        </div>

        <slot :value="value"/>
    </div>
</template>

<script>
export default {
    props: {
        default: { default: null },
    },

    data() {
        return {
            value: this.default,
        }
    },

    computed: {
        tab() {
            const vnode = this.$slots.default && this.$slots.default.find(
                elm => elm.child && elm.child.value == this.value
            );
            return vnode && vnode.child;
        }
    },

    methods: {
        selectTab(tab) {
            const value = tab.value;
            if(this.value === value)
                return;

            this.value = value;
            this.$emit('select', {target: this, value: value, tab: tab});
        },
    },
}
</script>


