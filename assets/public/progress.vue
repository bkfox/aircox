<template>
    <div class="media">
        <div class="media-left">
            <slot name="value" :value="valueDisplay" :max="max">{{ format(valueDisplay) }}</slot>
        </div>
        <div ref="bar" class="media-content" @click.stop="onClick" @mouseleave.stop="onMouseMove"
                @mousemove.stop="onMouseMove">
            <div :class="progressClass" :style="progressStyle">&nbsp;</div>
        </div>
        <div class="media-right">
            <slot name="value" :value="valueDisplay" :max="max">{{ format(max) }}</slot>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            hoverValue: null,
        }
    },

    props: {
        value: Number,
        max: Number,
        format: { type: Function, default: x => x },
        progressClass: { default: 'has-background-primary' },
        vertical: { type: Boolean, default: false },
    },

    computed: {
        valueDisplay() { return this.hoverValue === null ? this.value : this.hoverValue; },

        progressStyle() {
            if(!this.max)
                return null;
            let value = this.max ? this.valueDisplay * 100 / this.max : 0;
            return this.vertical ? { height: `${value}%` } : { width: `${value}%` };
        },
    },

    methods: {
        xToValue(x) { return x * this.max / this.$refs.bar.getBoundingClientRect().width },
        yToValue(y) { return y * this.max / this.$refs.bar.getBoundingClientRect().height },

        valueFromEvent(event) {
            let rect = event.currentTarget.getBoundingClientRect()
            return this.vertical ? this.yToValue(event.clientY - rect.y)
                                 : this.xToValue(event.clientX - rect.x);
        },

        onClick(event) {
            this.$emit('select', this.valueFromEvent(event));
        },

        onMouseMove(event) {
            if(event.type == 'mouseleave')
                this.hoverValue = null;
            else {
                this.hoverValue = this.valueFromEvent(event);
            }
        },
    },
}
</script>

