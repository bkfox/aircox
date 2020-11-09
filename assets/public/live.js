import {setEcoTimeout} from 'public/utils';
import Model from './model';

export default class Live {
    constructor({url,timeout=10,src=""}={}) {
        this.url = url;
        this.timeout = timeout;
        this.src = src;

        this.promise = null;
        this.items = [];
    }

    get current() {
        let item = this.items && this.items[this.items.length-1];
        if(item)
            item.src = this.src;
        return item ? new Model(item) : null;
    }

    //-- data refreshing
    drop() {
        this.promise = null;
    }

    fetch() {
        const promise = fetch(this.url).then(response =>
            response.ok ? response.json()
                        : Promise.reject(response)
        ).then(data => {
            this.items = data;
            return this.items
        })

        this.promise = promise;
        return promise;
    }

    refresh() {
        const promise = this.fetch();
        promise.then(data => {
            if(promise != this.promise)
                return [];

            setEcoTimeout(() => this.refresh(), this.timeout*1000)
        })
        return promise
    }
}

