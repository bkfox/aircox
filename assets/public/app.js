import Vue from 'vue';

export const defaultConfig = {
    el: '#app',
    delimiters: ['[[', ']]'],

    computed: {
        player() { return window.aircox.player; },
    },
}


export default class AppBuilder {
    constructor(config={}) {
        this._config = config;
        this.title = null;
        this.app = null;
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

    destroy() {
        self.app && self.app.$destroy();
        self.app = null;
    }

    fetch(url, options) {
        return fetch(url, options).then(response => response.text())
            .then(content => {
                let doc = new DOMParser().parseFromString(content, 'text/html');
                let app = doc.getElementById('app');
                content = app ? app.innerHTML : content;
                return this.load({sync: true, content, title: doc.title, url })
            })
    }

    load({async=false,content=null,title=null}={}) {
        var self = this;
        return new Promise((resolve, reject) => {
            let func = () => {
                try {
                    let config = self.config;
                    const el = document.querySelector(config.el);
                    if(!el)
                        return reject(`Error: can't get element ${config.el}`)

                    if(content)
                        el.innerHTML = content
                    if(title)
                        document.title = title;
                    this.app = new Vue(config);
                    resolve(self.app)
                } catch(error) {
                    self.destroy();
                    reject(error)
                }};
            async ? window.addEventListener('load', func) : func();
        });
    }

    /// Save application state into browser history
    historySave(url,replace=false) {
        const el = document.querySelector(this.config.el);
        const state = {
            content: el.innerHTML,
            title: document.title,
        };

        if(replace)
            history.replaceState(state, '', url)
        else
            history.pushState(state, '', url)
    }

    /// Load application from browser history's state
    historyLoad(state) {
        return this.load({ content: state.content, title: state.title });
    }
}


