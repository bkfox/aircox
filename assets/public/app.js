import Vue from 'vue';

export const defaultConfig = {
    el: '#app',
    delimiters: ['[[', ']]'],

    data() {
        return {
            page: null,
        }
    },

    computed: {
        player() { return window.aircox.player; },
    },
}

export default function App(config, sync=false) {
    return (new AppConfig(config)).load(sync)
}

/**
 * Application config for an application instance
 */
export class AppConfig {
    constructor(config) {
        this._config = config;
    }

    get config() {
        let config = this._config instanceof Function ? this._config() : this._config;
        for(var k of new Set([...Object.keys(config || {}), ...Object.keys(defaultConfig)])) {
            if(!config[k] && defaultConfig[k])
                config[k] = defaultConfig[k]
            else if(config[k] instanceof Object)
                config[k] = {...defaultConfig[k], ...config[k]}
        }
        return config;
    }

    set config(value) {
        this._config = value;
    }

    load(sync=false) {
        var self = this;
        return new Promise(function(resolve, reject) {
            let func = () => { try { resolve(self.build()) } catch(error) { reject(error) }};
            sync ? func() : window.addEventListener('load', func);
        });
    }

    build() {
        let config = this.config;
        const el = document.querySelector(config.el)
        if(!el) {
            reject(`Error: missing element ${config.el}`);
            return;
        }
        return new Vue(config);
    }
}


