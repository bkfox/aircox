import Vue from 'vue';

import Model from 'public/model';


export class Streamer extends Model {
    get queues() { return this.data ? this.data.queues : []; }
    get playlists() { return this.data ? this.data.playlists : []; }
    get sources() { return [...this.queues, ...this.playlists]; }
    get source() { return this.sources.find(o => o.id == this.data.source) }

    commit(data) {
        if(!this.data)
            this.data = { id: data.id, playlists: [], queues: [] }

        data.playlists = Playlist.updateList(data.playlists, this.playlists)
        data.queues = Queue.updateList(data.queues, this.queues)
        super.commit(data)
    }
}

export class Request extends Model {
    static getId(data) { return data.rid; }
}

export class Source extends Model {
    constructor(...args) {
        super(...args);
        setInterval(() => this.tick(), 1000)
    }

    get isQueue() { return false; }
    get isPlaylist() { return false; }
    get isPlaying() { return this.data.status == 'playing' }
    get isPaused() { return this.data.status == 'paused' }

    get remainingString() {
        if(!this.remaining)
            return '00:00';

        const seconds = Math.floor(this.remaining % 60);
        const minutes = Math.floor(this.remaining / 60);
        return String(minutes).padStart(2, '0') + ':' +
               String(seconds).padStart(2, '0');
    }


    sync() { return this.action('sync/', {method: 'POST'}, true); }
    skip() { return this.action('skip/', {method: 'POST'}, true); }
    restart() { return this.action('restart/', {method: 'POST'}, true); }

    seek(count) {
        return this.action('seek/', {
            method: 'POST',
            body: JSON.stringify({count: count})
        }, true)
    }

    tick() {
        if(!this.data.remaining || !this.isPlaying)
            return;
        const delta = (Date.now() - this.commitDate) / 1000;
        Vue.set(this, 'remaining', this.data.remaining - delta)
    }

    commit(data) {
        if(data.air_time)
            data.air_time = new Date(data.air_time);
        Vue.set(this, 'remaining', data.remaining)
        this.commitDate = Date.now()
        super.commit(data)
    }
}


export class Playlist extends Source {
    get isPlaylist() { return true; }
}


export class Queue extends Source {
    get isQueue() { return true; }
    get queue() { return this.data && this.data.queue; }

    commit(data) {
        data.queue = Request.updateList(data.queue, this.queue)
        super.commit(data)
    }

    push(soundId) {
        return this.action('push/', {
            method: 'POST',
            body: JSON.stringify({'sound_id': parseInt(soundId)})
        }, true);
    }
}


