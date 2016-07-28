// TODO
// - multiple sources for an item
// - live streams as item;
// - add to playlist button
//

/// Return a human-readable string from seconds
function duration_str(seconds) {
    seconds = Math.floor(seconds);
    var hours = Math.floor(seconds / 3600);
    seconds -= hours;
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes;

    var str = hours ? (hours < 10 ? '0' + hours : hours) + ':' : '';
    str += (minutes < 10 ? '0' + minutes : minutes) + ':';
    str += (seconds < 10 ? '0' + seconds : seconds);
    return str;
}


function Sound(title, detail, stream, duration) {
    this.title = title;
    this.detail = detail;
    this.stream = stream;
    this.duration = duration;
}

Sound.prototype = {
    title: '',
    detail: '',
    stream: '',
    duration: undefined,

    item: undefined,

    get seekable() {
        return this.duration != undefined;
    },
}


function PlayerPlaylist(player) {
    this.player = player;
    this.playlist = player.player.querySelector('.playlist');
    this.item_ = player.player.querySelector('.playlist .item');
    this.items = []
}

PlayerPlaylist.prototype = {
    items: undefined,

    find: function(stream) {
        return this.items.find(function(stream_) {
            return stream_ == stream;
        });
    },

    add: function(sound, container) {
        if(this.find(sound.stream))
            return;

        var item = this.item_.cloneNode(true);
        item.removeAttribute('style');

        console.log(sound)
        item.querySelector('.title').innerHTML = sound.title;
        if(sound.seekable)
            item.querySelector('.duration').innerHTML =
                duration_str(sound.duration);
        if(sound.detail)
            item.querySelector('.detail').href = sound.detail;

        item.sound = sound;
        sound.item = item;

        var self = this;
        item.querySelector('.action.remove').addEventListener(
            'click', function(event) { self.remove(sound); }, false
        );

        (container || this.playlist).appendChild(item);
        this.items.push(sound);
        this.save();
    },

    remove: function(sound) {
        var index = this.items.indexOf(sound);
        if(index != -1)
            this.items.splice(index,1);
        this.playlist.removeChild(sound.item);
        this.save();
    },

    save: function() {
        var list = [];
        for(var i in this.items) {
            var sound = Object.assign({}, this.items[i])
            delete sound.item;
            list.push(sound);
        }
        this.player.store.set('playlist', list);
    },

    load: function() {
        var list = [];
        var container = document.createDocumentFragment();
        for(var i in list)
            this.add(list[i], container)
        this.playlist.appendChild(container);
    },
}


function Player(id) {
    this.store = new Store('player');

    // html items
    this.player = document.getElementById(id);
    this.box = this.player.querySelector('.box');
    this.audio = this.player.querySelector('audio');
    this.controls = {
        duration: this.box.querySelector('.duration'),
        progress: this.player.querySelector('progress'),
        single: this.player.querySelector('input.single'),
    }

    this.playlist = new PlayerPlaylist(this);
    this.playlist.load();

    this.init_events();
    this.load();
}

Player.prototype = {
    /// current item being played
    sound: undefined,

    init_events: function() {
        var self = this;

        function time_from_progress(event) {
            bounding = self.controls.progress.getBoundingClientRect()
            offset = (event.clientX - bounding.left);
            return offset * self.audio.duration / bounding.width;
        }

        function update_info() {
            var controls = self.controls;
            // progress
            if( !self.sound.seekable ||
                    self.audio.duration == Infinity) {
                controls.duration.innerHTML = '';
                controls.progress.value = 0;
                return;
            }

            var pos = self.audio.currentTime;
            controls.progress.value = pos;
            controls.progress.max = self.audio.duration;
            controls.duration.innerHTML = duration_str(sound.duration);
        }

        // audio
        this.audio.addEventListener('playing', function() {
            self.player.setAttribute('state', 'playing');
        }, false);

        this.audio.addEventListener('pause', function() {
            self.player.setAttribute('state', 'paused');
        }, false);

        this.audio.addEventListener('loadstart', function() {
            self.player.setAttribute('state', 'stalled');
        }, false);

        this.audio.addEventListener('loadeddata', function() {
            self.player.removeAttribute('state');
        }, false);

        this.audio.addEventListener('timeupdate', update_info, false);

        this.audio.addEventListener('ended', function() {
            if(!self.controls.single.checked)
                self.next(true);
        }, false);

        // buttons
        this.box.querySelector('button.play').onclick = function() {
            self.play();
        };

        // progress
        progress = this.controls.progress;
        progress.addEventListener('click', function(event) {
            player.audio.currentTime = time_from_progress(event);
        }, false);

        progress.addEventListener('mouseout', update_info, false);

        progress.addEventListener('mousemove', function(event) {
            if(self.audio.duration == Infinity)
               return;

            var pos = time_from_progress(event);
            self.controls.duration.innerHTML = duration_str(pos);
        }, false);
    },

    play: function() {
        if(this.audio.paused)
            this.audio.play();
        else
            this.audio.pause();
    },

    unselect: function(sound) {
        sound.item.removeAttribute('selected');
    },

    select: function(sound, play = true) {
        if(this.sound)
            this.unselect(this.sound);

        this.audio.pause();

        // if stream is a list, use <source>
        if(sound.stream.splice) {
            this.audio.src="";

            var sources = this.audio.querySelectorAll('source');
            for(var i in sources)
                this.audio.removeChild(sources[i]);

            for(var i in sound.stream) {
                var source = document.createElement('source');
                source.src = sound.stream[i];
            }
        }
        else
            this.audio.src = sound.stream;
        this.audio.load();

        this.sound = sound;
        sound.item.setAttribute('selected', 'true');

        this.box.querySelector('.title').innerHTML = sound.title;
        if(play)
            this.play();
    },

    next: function() {
        var index = this.playlist.items.indexOf(this.sound);
        if(index < 0)
            return;

        index++;
        if(index < this.playlist.items.length)
            this.select(this.playlist.items[index], true);
    },

    save: function() {
        this.store.set('player', {
            single: this.controls.single.checked,
            sound: this.sound && this.sound.stream,
        });
    },

    load: function() {
        var data = this.store.get('player');
        this.controls.single.checked = data.single;
        this.sound = this.playlist.find(data.stream);
    },

    update_on_air: function() {

    },
}


