<template>
    <div class="media">
        <div class="media-left">
            <slot name="value" :value="value" :max="max">{{ format(value) }}</slot>
        </div>
        <div ref="bar" class="media-content" @click.stop="onClick">
            <div :class="progressClass" :style="progressStyle">&nbsp;</div>
        </div>
        <div class="media-right">
            <slot name="value" :value="value" :max="max">{{ format(max) }}</slot>
        </div>
    </div>
</template>

<script>
export default {
    props: {
        value: Number,
        max: Number,
        format: { type: Function, default: x => x },
        progressClass: { default: 'has-background-primary' },
        vertical: { type: Boolean, default: false },
    },

    computed: {
        progressStyle() {
            if(!this.max)
                return null;
            return this.vertical ? { height: (this.max ? this.value * 100 / this.max : 0) + '%' }
                                 : { width: (this.max ? this.value * 100 / this.max : 0) + '%' };
        },
    },

    methods: {
        xToValue(x) { return x * this.max / this.$refs.bar.getBoundingClientRect().width },
        yToValue(y) { return y * this.max / this.$refs.bar.getBoundingClientRect().height },

        onClick(event) {
            let rect = event.currentTarget.getBoundingClientRect()
            this.$emit('select', this.vertical ? this.yToValue(event.clientY - rect.y)
                                               : this.xToValue(event.clientX - rect.x));
        },
    },
}
</script>

