<template>
    <form ref="form">
        <slot :counts="counts"></slot>
    </form>
</template>

<script>

const splitReg = new RegExp(`,\s*`, 'g');

export default {
    data() {
        return {
            counts: {},
        }
    },

    methods: {
        update() {
            const items = this.$el.querySelectorAll('input[name="data"]:checked')
            const counts = {};

            console.log(items)
            for(var item of items)
                if(item.value)
                    for(var tag of item.value.split(splitReg))
                        counts[tag.trim()] = (counts[tag.trim()] || 0) + 1;
            this.counts = counts;
            console.log('counts', this.counts)
        }
    },

    mounted() {
        this.$refs.form.addEventListener('change', () => this.update())
        this.update()
    }
}
</script>

