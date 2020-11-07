<template>
    <div>
        <slot></slot>
    </div>
</template>

<script>
export default {
    data() {
        return {}
    },

    props: {
        page: Object,
        title: String,
    },
}
</script>


