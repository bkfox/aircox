<template>
    <div>
        <slot :page="page" :podcasts="podcasts"></slot>
    </div>
</template>

<script>
import {Set} from './model';
import Sound from './sound';
import Page from './page';

export default {
    extends: Page,

    data() {
        return {
            podcasts: new Set(Sound, {items:this.page.podcasts}),
        }
    },
}
</script>


