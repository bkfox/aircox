<template>
    <div>
        <a-tabs class="tabs" @select="value = $event.value;">
            <template v-slot:default><slot name="tabs" :value="value"/></template>
        </a-tabs>

        <slot :value="value"></slot>
    </div>
</template>


<script>
import Tabs from './tabs.vue';

export default {
    props: ['default'],

    data() {
        return {
            value: this.default,
        }
    },

    components: {
        'a-tabs': Tabs,
    }
}
</script>
