<template>
    <div class="control">
        <Autocomplete ref="autocomplete" :data="data" :placeholder="placeholder" :field="field"
            :loading="isFetching" open-on-focus
            @typing="fetch" @select="object => onSelect(object)"
            >
        </Autocomplete>
        <input v-if="valueField" ref="value" type="hidden" :name="valueField"
            :value="selected && selected[valueAttr || valueField]" />
    </div>
</template>

<script>
import debounce from 'lodash/debounce'
import {Autocomplete} from 'buefy/dist/components/autocomplete';
import Vue from 'vue';

export default {
    props: {
        url: String,
        model: Function,
        placeholder: String,
        field: {type: String, default: 'value'},
        count: {type: Number, count: 10},
        valueAttr: String,
        valueField: String,
    },

    data() {
        return {
            data: [],
            selected: null,
            isFetching: false,
        };
    },

    methods: {
        onSelect(option) {
            console.log('selected', option)
            Vue.set(this, 'selected', option);
            this.$emit('select', option);
        },

        fetch: debounce(function(query) {
            if(!query)
                return;

            this.isFetching = true;
            this.model.fetchAll(this.url.replace('${query}', query))
                .then(data => {
                    this.data = data;
                    this.isFetching = false;
                }, data => { this.isFetching = false; Promise.reject(data) })
        }),
    },

    components: {
        Autocomplete,
    },
}

</script>

