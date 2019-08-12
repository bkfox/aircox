<template>
    <div class="media">
        <!-- TODO HERE -->
    </div>

</template>

<script>

export default {
    props: {
        url: String,
        timeout: Number,
    },

    data() {
        return {
            // promise is set to null on destroy: this is used as check
            // for timeout to know wether to repeat itself or not.
            promise: null,
            // on air infos
            on_air: null
        }
    },


    methods: {
        fetch() {
            const promise = fetch(url).then(response =>
                reponse.ok ? response.json
                           : Promise.reject(response)
            ).then(data => {
                this.on_air = data.results;
                return this.on_air
            })

            this.promise = promise;
            return promise;
        },

        refresh() {
            const promise = this.fetch();
            promise.then(data => {
                if(promise != this.promise)
                    return;

                window.setTimeout(() => this.update(), this.timeout*1000)
            })
        },
    },

    mounted() {
        this.update()
    },

    destroyed() {
        this.promise = null;
    }

}
</script>


