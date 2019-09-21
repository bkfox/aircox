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


// TODO: move in another module for reuse
export default class Model {
    constructor(data, {url=null}={}) {
        this.commit(data);
    }

    static getId(data) {
        return data.id;
    }

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

    static fetch(url, options=null, initArgs=null) {
        options = this.getOptions(options)
        return fetch(url, options)
            .then(response => response.json())
            .then(data => new this(d, {url: url, ...initArgs}));
    }

    static fetchAll(url, options=null, initArgs=null) {
        options = this.getOptions(options)
        return fetch(url, options)
            .then(response => response.json())
            .then(data => {
                if(!(data instanceof Array))
                    data = data.results;
                data = data.map(d => new this(d, {baseUrl: url, ...initArgs}));
                return data
            })
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
        this.url = data.url_;
        Vue.set(this, 'data', data);
    }

    /**
     * Return data as model with url prepent by `this.url`.
     */
    asChild(model, data, prefix='') {
        return new model(data, {baseUrl: `${this.url}${prefix}/`})
    }

    getChildOf(attr, id) {
        const index = this.data[attr].findIndex(o => o.id = id)
        return index == -1 ? null : this.data[attr][index];
    }

    static updateList(list=[], old=[]) {
         return list.reduce((items, data) => {
            const id = this.getId(data);
            let [index, obj] = [old.findIndex(o => o.id == id), null];
            if(index != -1) {
                old[index].commit(data)
                items.push(old[index]);
            }
            else
                items.push(new this(data))
            return items;
        }, [])
    }
}


