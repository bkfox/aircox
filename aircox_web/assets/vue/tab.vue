<template>
    <li @click.prevent="onclick"
        :class="{'is-active': $parent.value == value}">
        <slot></slot>
    </li>
</template>

<script>
export default {
    props: {
        value: { default: undefined },
    },

    methods: {
        select() {
            this.$parent.selectTab(this);
        },

        onclick(event) {
            this.select();
            /*if(event.target.href != document.location)
                window.history.pushState(
                    { url: event.target.href },
                    event.target.innerText + ' - ' + document.title,
                    event.target.href
                ) */
        }
    }
}
</script>

