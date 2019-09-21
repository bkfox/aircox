import Vue from 'vue';


export const appBaseConfig = {
    el: '#app',
    delimiters: ['[[', ']]'],
}

/**
 * Application config for the main application instance
 */
var appConfig = {};

export function setAppConfig(config) {
    for(var member in appConfig) delete appConfig[member];
    return Object.assign(appConfig, config)
}

export function getAppConfig(config) {
    if(config instanceof Function)
        config = config()
    config = config == null ? appConfig : config;
    return {...appBaseConfig, ...config}
}


/**
 * Create Vue application at window 'load' event and return a Promise
 * resolving to the created app.
 *
 * config: defaults to appConfig (checked when window is loaded)
 */
export function loadApp(config=null) {
    return new Promise(function(resolve, reject) {
        window.addEventListener('load', function() {
            try {
                config = getAppConfig(config)
                const el = document.querySelector(config.el)
                if(!el) {
                    reject(`Error: missing element ${config.el}`);
                    return;
                }

                resolve(new Vue(config))
            }
            catch(error) { reject(error) }
        })
    })
}




