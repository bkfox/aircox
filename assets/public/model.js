import Vue from 'vue';

function getCookie(name) {
    if(document.cookie && document.cookie !== '') {
        const cookie = document.cookie.split(';')
                               .find(c => c.trim().startsWith(name + '='))
        return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
    }
    return null;
}

var csrfToken = null;

export function getCsrf() {
    if(csrfToken === null)
        csrfToken = getCookie('csrftoken')
    return csrfToken;
}


// TODO: prevent duplicate simple fetch
export default class Model {
    constructor(data, {url=null}={}) {
        this.url = url;
        this.commit(data);
    }

    /**
     * Get instance id from its data
     */
    static getId(data) {
        return data.id;
    }

    /**
     * Return fetch options
     */
    static getOptions(options) {
        return {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': getCsrf(),
            },
            ...options,
        }
    }

    /**
     * Fetch item from server
     */
    static fetch(url, options=null, args=null) {
        options = this.getOptions(options)
        return fetch(url, options)
            .then(response => response.json())
            .then(data => new this(data, {url: url, ...args}));
    }

    /**
     * Fetch data from server.
     */
    fetch(options) {
        options = this.constructor.getOptions(options)
        return fetch(this.url, options)
            .then(response => response.json())
            .then(data => this.commit(data));
    }

    /**
     * Call API action on object.
     */
    action(path, options, commit=false) {
        options = this.constructor.getOptions(options)
        const promise = fetch(this.url + path, options);
        return commit ? promise.then(data => data.json())
                               .then(data => { this.commit(data); this.data })
                      : promise;
    }

    /**
     * Update instance's data with provided data. Return None
     */
    commit(data) {
        this.id = this.constructor.getId(data);
        Vue.set(this, 'data', data);
    }

    /**
     * Save instance into localStorage.
     */
    store(key) {
        window.localStorage.setItem(key, JSON.stringify(this.data));
    }

    /**
     * Load model instance from localStorage.
     */
    static storeLoad(key) {
        let item = window.localStorage.getItem(key);
        return item === null ? item : new this(JSON.parse(item));
    }
}


/**
 * List of models
 */
export class Set {
    constructor(model, {items=[],url=null,args={},unique=null,max=null,storeKey=null}={}) {
        this.items = items.map(x => x instanceof model ? x : new model(x, args));
        this.model = model;
        this.url = url;
        this.unique = unique;
        this.max = max;
        this.storeKey = storeKey;
    }

    get length() { return this.items.length }
    indexOf(...args) { return this.items.indexOf(...args); }

    /**
     * Fetch multiple items from server
     */
    static fetch(url, options=null, args=null) {
        options = this.getOptions(options)
        return fetch(url, options)
            .then(response => response.json())
            .then(data => (data instanceof Array ? data : data.results)
                              .map(d => new this.model(d, {url: url, ...args})))
    }

    /**
     * Load list from localStorage
     */
    static storeLoad(model, key, args={}) {
        let items = window.localStorage.getItem(key);
        return new this(model, {...args, storeKey: key, items: items ? JSON.parse(items) : []});
    }

    /**
     * Store list into localStorage
     */
    store() {
        if(this.storeKey)
            window.localStorage.setItem(this.storeKey, JSON.stringify(
                this.items.map(i => i.data)));
    }

    push(item, {args={}}={}) {
        item = item instanceof this.model ? item : new this.model(item, args);
        if(this.unique && this.items.find(x => x.id == item.id))
            return;
        if(this.max && this.items.length >= this.max)
            this.items.splice(0,this.items.length-this.max)

        this.items.push(item);
        this._updated()
    }

    remove(item, {args={}}={}) {
        item = item instanceof this.model ? item : new this.model(item, args);
        let index = this.items.findIndex(x => x.id == item.id);
        if(index == -1)
            return;

        this.items.splice(index,1);
        this._updated()
    }

    _updated() {
        Vue.set(this, 'items', this.items);
        this.store();
    }
}

Set[Symbol.iterator] = function () {
    return this.items[Symbol.iterator]();
}

