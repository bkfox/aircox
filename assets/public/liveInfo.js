
export default class {
    constructor(url, timeout) {
        this.url = url;
        this.timeout = timeout;
        this.promise = null;
        this.items = [];
    }

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

            window.setTimeout(() => this.refresh(), this.timeout*1000)
        })
        return promise
    }
}
