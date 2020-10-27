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
        player() { return window.aircox.player; }
    },
}

export default function App(config) {
    return (new AppConfig(config)).load()
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
        return {...defaultConfig, ...config};
    }

    set config(value) {
        this._config = value;
    }

    load() {
        var self = this;
        return new Promise(function(resolve, reject) {
            window.addEventListener('load', () => {
                try {
                    let config = self.config;
                    const el = document.querySelector(config.el)
                    if(!el) {
                        reject(`Error: missing element ${config.el}`);
                        return;
                    }
                    resolve(new Vue(config))
                }
                catch(error) { reject(error) }
            })
        });
    }
}


