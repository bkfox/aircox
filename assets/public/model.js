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
        this.items = [];
        this.model = model;
        this.url = url;
        this.unique = unique;
        this.max = max;
        this.storeKey = storeKey;

        for(var item of items)
            this.push(item, {args: args, save: false});
    }

    get length() { return this.items.length }

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
        this.storeKey && window.localStorage.setItem(this.storeKey, JSON.stringify(
            this.items.map(i => i.data)));
    }

    /**
     * Save item
     */
    save() {
        this.storeKey && this.store();
    }

    /**
     * Get item at index
     */
    get(index) { return this.items[index] }

    /**
     * Find an item by id or using a predicate function
     */
    find(pred) {
        return pred instanceof Function ? this.items.find(pred)
                                        : this.items.find(x => x.id == pred.id);
    }

    /**
     * Find item index by id or using a predicate function
     */
    findIndex(pred) {
        return pred instanceof Function ? this.items.findIndex(pred)
                                        : this.items.findIndex(x => x.id == pred.id);
    }

    /**
     * Add item to set, return index.
     */
    push(item, {args={},save=true}={}) {
        item = item instanceof this.model ? item : new this.model(item, args);
        if(this.unique) {
            let index = this.findIndex(item);
            if(index > -1)
                return index;
        }
        if(this.max && this.items.length >= this.max)
            this.items.splice(0,this.items.length-this.max)

        this.items.push(item);
        save && this.save();
        return this.items.length-1;
    }

    /**
     * Remove item from set by index
     */
    remove(index, {save=true}={}) {
        this.items.splice(index,1);
        save && this.save();
    }
}

Set[Symbol.iterator] = function () {
    return this.items[Symbol.iterator]();
}

